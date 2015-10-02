#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from active_applications_qtmodel import active_applications_qtmodel
from rules_model_qt import rules_model_qt

import track_base

from PyQt4.QtCore import pyqtSlot

import zmq
import json
import logging

log = logging.getLogger('time_tracker_qt')


class time_tracker_qt():
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self, parent):
        self._req_socket = None
        self._current_data = None
        self._initialized = False

        self._active_day = track_base.today_int()

        self._applications = active_applications_qtmodel(parent)
        self._rules = rules_model_qt(parent)
        self._rules.modified_rules.connect(self.update_categories)

    def __eq__(self, other):
        return False

    def connect(self):
        self._req_socket = zmq.Context().socket(zmq.REQ)

        self._req_socket.connect('tcp://127.0.0.1:3456')

        self._req_socket.send_json({'type': 'version'})
        log.info('server version: %s', self._req_socket.recv_json())

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def get_applications_model(self):
        return self._applications

    def get_rules_model(self):
        return self._rules

    def update(self):
        log.info('update')
        
        self._req_socket.send_json({'type': 'current'})
        received_data = self._req_socket.recv_json()
        if not 'current' in received_data:
            raise
        self._current_data = received_data['current']
        
        self._req_socket.send_json({'type': 'current'})
        received_data = self._req_socket.recv_json()
        if not 'current' in received_data:
            raise
        self._current_data = received_data['current']
        
        self._initialized = True
    
    def initialized(self):
        return self._initialized

    def info(self, minute):
        return self._applications.info(minute)

    def begin_index(self):
        return self._applications.begin_index()

    def start_time(self):
        _s = self._applications.begin_index()
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def now(self):
        _s = self._current_data['minute']
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

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

    @pyqtSlot()
    def update_categories(self):
        self._applications.update_all_categories(self._rules.get_first_matching_key)

    def new_regex_rule(self):
        self._rules.add_rule()
