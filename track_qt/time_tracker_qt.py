#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from track_qt.active_applications_qtmodel import active_applications_qtmodel
from track_qt.rules_model_qt import rules_model_qt

import track_base

from PyQt5.QtCore import pyqtSlot

import zmq
import logging

log = logging.getLogger('time_tracker_qt')

class server_timeout(Exception):
    pass

class time_tracker_qt:
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self, parent):
        self._req_socket = None
        self._req_poller = None
        self._receiving = False

        self._current_data = None
        self._initialized = False
        self._connected = False

        self._active_day = track_base.today_int()

        self._applications = active_applications_qtmodel(parent)
        self._rules = rules_model_qt(parent)
        self._rules.modified_rules.connect(self.update_categories)

        self._req_poller = zmq.Poller()
        self._zmq_context = zmq.Context()

    def __eq__(self, other):
        return False

    def _req_send(self, msg):
        if self._receiving:
            raise Exception('wrong send/recv state!')
        self._receiving = True
        self._req_socket.send_json(msg)

    def _req_recv(self, timeout, raise_on_timeout):
        if not self._receiving:
            raise Exception('wrong send/recv state!')
        self._receiving = False
        _timeout = timeout
        while True:
            if self._req_poller.poll(_timeout) == []:
                if raise_on_timeout:
                    raise server_timeout("timeout on recv()")
                log.warning('server timeout. did you even start one?')
                _timeout = 2000
                continue
            break
        return self._req_socket.recv_json()

    def _request(self, msg, timeout=50, raise_on_timeout=False):
        if not self._connected:
            raise track_base.not_connected()
        self._req_send(msg)
        return self._req_recv(timeout, raise_on_timeout)

    def connect(self, endpoint):
        if self._req_socket:
            self._req_poller.unregister(self._req_socket)
            self._req_socket.close()

        self._req_socket = self._zmq_context.socket(zmq.REQ)
        self._req_poller.register(self._req_socket, zmq.POLLIN)
        self._req_socket.connect(endpoint)
        self._check_version()
        self._connected = True
        self._fetch_rules()

    def _check_version(self):
        with track_base.frame_grabber(log):
            self._req_send({'type': 'version'})
            _version = self._req_recv(timeout=1000, raise_on_timeout=True)
            log.info('server version: %s', _version)

    def _fetch_rules(self):
        with track_base.frame_grabber(log):
            _received_data = self._request({'type': 'rules'})
            self._rules.from_dict(_received_data)
            if not 'rules' in _received_data:
                raise

    def save(self):
        with track_base.frame_grabber(log):
            _received_data = self._request({'type': 'save'})

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def get_applications_model(self):
        return self._applications

    def get_rules_model(self):
        return self._rules

    def update(self):
        with track_base.frame_grabber(log):

            received_data = self._request({'type': 'current'})
            if not 'current' in received_data:
                raise
            self._current_data = received_data['current']

            received_data = self._request({'type': 'apps'})
            if not 'apps' in received_data:
                raise
            self._applications.from_dict(received_data['apps'])

            self._initialized = True

    def initialized(self):
        return self._initialized

    def info(self, minute):
        return self._applications.info(minute)

    def begin_index(self):
        return self._applications.begin_index()

    def start_time(self):
        _s = self._applications.begin_index()
        return("%0.2d:%0.2d" % (int(_s / 60), _s % 60))

    def now(self):
        _s = self._current_data['minute']
        return("%0.2d:%0.2d" % (int(_s / 60), _s % 60))

    def is_active(self, minute):
        return self._applications.is_active(minute)

    def is_private(self, minute):
        return self._applications.is_private(minute)

    def get_time_total(self):
        return self._current_data['time_total']

    def get_time_active(self):
        return len(self._applications._minutes)

    def get_time_work(self):
        r = 0
        for i, m in self._applications._minutes.items():
            r += 1 if str(m._category) != "0" else 0
        return r

    def get_time_private(self):
        r = 0
        for i, m in self._applications._minutes.items():
            r += str(m._category) == "0"
        return r

    def get_time_per_categories(self):
        ##TODO: cache this, so you don't do so many operations per second.
        ##This is pretty inneficient
        time_dict={}
        for app_name in self._applications._apps:
            app = self._applications._apps[app_name]
            category=str(app._category)
            if(category in time_dict):
                time_dict[category] += app.get_count()
            else:
                time_dict[category] = app.get_count()
        return time_dict

    def get_time_idle(self):
        return self.get_time_total() - len(self._applications._minutes)

    def get_max_minute(self):
        return self._applications.end_index()

    def get_current_minute(self):
        return self._current_data['minute']

    def get_idle(self):
        return self._current_data['user_idle']

    def get_current_app_title(self):
        return self._current_data['app_title']

    def get_current_process_name(self):
        return self._current_data['process_name']

    def user_is_active(self):
        return self._current_data['user_active']

    #@pyqtSlot()
    def update_categories(self):
        self._applications.update_all_categories(self._rules.get_first_matching_key)

    def new_regex_rule(self):
        self._rules.add_rule()
