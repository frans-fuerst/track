#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Client side part of TrimeTracker
"""

from contextlib import suppress
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5 import QtWidgets  # type: ignore

import zmq  # type: ignore

from .active_applications_qtmodel import ActiveApplicationsModel
from .rules_model_qt import RulesModelQt
from .qt_common import TimechartDataprovider
from .. import core
from ..core.util import log
from ..core import errors


class TimeTrackerClientQt(TimechartDataprovider):
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

        self._current_data = {}
        self._initialized = False
        self.connected = False

        self._active_day = core.today_int()

        self._applications = ActiveApplicationsModel(parent)
        self._rules_model = RulesModelQt(parent=parent)
        self._rules_model.rulesChanged.connect(self.update_categories)
        self._date = datetime.now()

    def date(self):
        return self._date

    def initialized(self):
        return self._initialized

    def begin_index(self):
        return self._applications.begin_index()

    def end_index(self):
        return self._applications.end_index()

    def info_at(self, minute: int):
        return self._applications.info_at(minute)

    def category_at(self, minute: int):
        return self._applications.category_at(minute)

    def current_minute(self):
        return self._current_data.get('minute', 0)

    def time_total(self):
        return self.end_index() - self.begin_index() + 1

    def time_active(self):
        return len(self._applications._minutes)

    def time_work(self):
        return sum(minute.main_category() == 2 for _, minute in self._applications._minutes.items())

    def time_private(self):
        return sum(minute.main_category() == 3 for _, minute in self._applications._minutes.items())

    def time_idle(self):
        return self.time_total() - len(self._applications._minutes)

    def clip_from(self, index: str) -> None:
        self._request("clip_from", data={"index": index})

    def clip_to(self, index: int) -> None:
        self._request("clip_to", data={"index": index})

    def clear(self) -> None:
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
                 data: Optional[Dict[str, Any]]=None,
                 timeout: str=50,
                 raise_on_timeout: bool = False) -> Dict[str, Any]:
        def result_or_exception(result):
            if result.get("type") == "error":
                raise RuntimeError(result["what"])
            return result.get("data")
        if not self.connected:
            raise errors.NotConnected("Tried to send request while not connected to server")
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
        server_version = self._req_recv(timeout=1000, raise_on_timeout=True)["data"]["version"]
        if server_version > str(core.version_info):
            log().critical('Server version: %s', server_version)
        elif server_version < str(core.version_info):
            log().error('Server version: %s', server_version)
        else:
            log().error('Server version: %s', server_version)

    def _fetch_rules(self):
        rules = self._request("rules").get("rules")
        self._rules_model.set_rules(rules)

    def note(self) -> str:
        return self._request("note").get("note")

    def save(self) -> None:
        self._request("save")

    def update(self) -> None:
        current_data = self._request("current").get("current")
        apps = self._request("apps").get("apps")

        assert current_data is not None and apps is not None

        self._current_data = current_data
        self._applications.from_dict(apps)

        self._initialized = True

    def update_categories(self):
        log().info("Category rules have changed")
        self._request("set_rules", data={"rules": self._rules_model.rules()})

    def set_note(self, text) -> None:
        self._request("set_note", data={"note": text})

    def quit_server(self):
        with suppress(RuntimeError):
            self._request("quit")
        self.connected = False

    def get_applications_model(self):
        return self._applications

    def rules_model(self):
        return self._rules_model

    def is_active(self, minute):
        return self._applications.is_active(minute)

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

    def get_current_category(self):
        return self._current_data['category']

    def get_idle(self):
        return self._current_data['user_idle']

    def get_current_app_title(self):
        return self._current_data['app_title']

    def get_current_process_name(self):
        return self._current_data['process_name']

    def user_is_active(self) -> bool:
        return self._current_data['user_active']
