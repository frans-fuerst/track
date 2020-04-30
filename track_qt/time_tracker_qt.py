#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Client side part of TrimeTracker
"""

from contextlib import suppress

from typing import Dict, Any, Optional
from PyQt5 import QtWidgets  # type: ignore

import zmq  # type: ignore

from track_base.util import log
from . import track_base
from . import ActiveApplicationsModel
from . import RulesModelQt


class TimeTrackerClientQt:
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self._req_socket = None  # type: Optional[zmq.Socket]
        self._req_poller = zmq.Poller()
        self._zmq_context = zmq.Context()
        self._receiving = False

        self._current_data = None
        self._initialized = False
        self.connected = False

        self._active_day = track_base.today_int()

        self._applications = ActiveApplicationsModel(parent)
        self._rules = RulesModelQt(parent=parent)
        self._rules.rulesChanged.connect(self.update_categories)

    def clear(self) -> None:
        # must not be overwritten - we need the instance
        self._applications.clear()

    def _req_send(self, msg: Dict[str, Any]) -> None:
        if self._receiving or self._req_socket is None:
            raise Exception('wrong send/recv state!')
        self._receiving = True
        self._req_socket.send_json(msg)

    def _req_recv(self, timeout: int, raise_on_timeout: bool) -> Dict[str, Any]:
        if not self._receiving or self._req_socket is None:
            raise Exception('wrong send/recv state!')
        self._receiving = False
        _timeout = timeout
        while True:
            if self._req_poller.poll(_timeout) == []:
                if raise_on_timeout:
                    raise TimeoutError("timeout on recv()")
                log().warning('server timeout. did you even start one?')
                _timeout = 2000
                continue
            break
        return self._req_socket.recv_json()

    def _request(self,
                 cmd: str,
                 *,
                 data: Optional[Dict[str, Any]] = None,
                 timeout: str = 50,
                 raise_on_timeout: bool = False) -> Dict[str, Any]:
        def result_or_exception(result):
            if result.get("type") == "error":
                raise RuntimeError(result["what"])
            return result.get("data")
        if not self.connected:
            raise RuntimeError("Tried to send request while not connected to server")
        self._req_send({"cmd": cmd, "data": data})
        return result_or_exception(self._req_recv(timeout, raise_on_timeout))

    def connect(self, endpoint: str) -> None:
        if self._req_socket:
            self._req_poller.unregister(self._req_socket)
            self._req_socket.close()

        self._req_socket = self._zmq_context.socket(zmq.REQ)
        self._req_poller.register(self._req_socket, zmq.POLLIN)
        self._req_socket.connect(endpoint)
        self._check_version()
        self.connected = True
        self._fetch_rules()

    def _check_version(self):
        self._req_send({"cmd": 'version'})
        _version = self._req_recv(timeout=1000, raise_on_timeout=True)
        log().info('server version: %s', _version)

    def _fetch_rules(self):
        rules = self._request("rules").get("rules")
        self._rules.set_rules(rules)

    def note(self) -> str:
        return self._request("note").get("note")

    def save(self) -> None:
        self._request("save")

    def clip_from(self, index: str) -> None:
        self._request("clip_from", data={"index": index})

    def clip_to(self, index: int) -> None:
        self._request("clip_to", data={"index": index})

    def update(self) -> None:
        current_data = self._request("current").get("current")
        apps = self._request("apps").get("apps")

        assert current_data is not None and apps is not None

        self._current_data = current_data
        self._applications.from_dict(apps)

        self._initialized = True

    def update_categories(self):
        log().info("Category rules have changed")
        self._request("set_rules", data={"rules": self._rules.rules()})

    def set_note(self, text) -> None:
        self._request("set_note", data={"note": text})

    def quit_server(self):
        with suppress(RuntimeError):
            self._request("quit")
        self.connected = False

    def initialized(self):
        return self._initialized

    def get_applications_model(self):
        return self._applications

    def get_rules_model(self):
        return self._rules

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

    def category_at(self, minute):
        return self._applications.category_at(minute)

    def get_time_total(self):
        return self._current_data['time_total']

    def get_time_active(self):
        return len(self._applications._minutes)

    def get_time_work(self):
        return sum(minute.main_category() == 2 for _, minute in self._applications._minutes.items())

    def get_time_private(self):
        return sum(minute.main_category() == 3 for _, minute in self._applications._minutes.items())

    def get_time_per_categories(self):
        # TODO: cache this, so you don't do so many operations per second.
        # This is pretty inneficient
        time_dict = {}
        for app_name in self._applications._apps:
            app = self._applications._apps[app_name]
            category = str(app._category)
            if category in time_dict:
                time_dict[category] += app.get_count()
            else:
                time_dict[category] = app.get_count()
        return time_dict

    def get_time_idle(self):
        return self.get_time_total() - len(self._applications._minutes)

    def get_max_minute(self):
        return self._applications.end_index()

    def get_current_category(self):
        return self._current_data['category']

    def get_current_minute(self):
        return self._current_data['minute']

    def get_idle(self):
        return self._current_data['user_idle']

    def get_current_app_title(self):
        return self._current_data['app_title']

    def get_current_process_name(self):
        return self._current_data['process_name']

    def user_is_active(self) -> bool:
        return self._current_data['user_active']
