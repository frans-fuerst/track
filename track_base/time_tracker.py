#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
log = logging.getLogger('base.time_tracker')

import desktop_usage_info

from track_base.active_applications import active_applications
from track_base.rules_model import rules_model
from track_base import track_common
import track_base


class time_tracker:
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self):
        self._idle_current = 0
        self._current_minute = 0  # does not need to be highest minute index
        self._current_app_title = ""
        self._current_process_exe = ""
        self._user_is_active = True
        self._active_day = track_common.today_int()
        self._storage_dir = 'track-storage'

        # -- persist
        self._applications = active_applications()
        self._rules = rules_model()

    def set_persistency_folder(self, path):
        self._storage_dir = os.path.expanduser(path)

    def __eq__(self, other):
        return False

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def load(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % track_common.today_str()
        # print(_file_name)
        try:
            with open(os.path.join(self._storage_dir, _file_name)) as _file:
                self._applications.from_dict(json.load(_file))
        except IOError:
            if filename is not None:
                log.warning('file "%s" does not exist', filename)

        self._rules.load(os.path.join(self._storage_dir, 'category_rules'))

    def save(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % track_common.today_str()
        # print(_file_name)
        _app_data = self._applications.__data__()
        try:
            track_base.make_dirs(self._storage_dir)
        except track_base.path_exists_error:
            pass

        with open(os.path.join(self._storage_dir, _file_name), 'w') as _file:
            json.dump(_app_data, _file,
                      sort_keys=True) #, indent=4, separators=(',', ': '))

        _test_model = active_applications()
        _test_model.from_dict(_app_data)
        assert self._applications == _test_model

        self._rules.save(os.path.join(self._storage_dir, 'category_rules'))

    def get_applications_model(self):
        return self._applications

    def get_rules_model(self):
        return self._rules

    def update(self):
        with track_base.frame_grabber(log):
            try:
                _today = track_common.today_int()
                self._current_minute = track_common.minutes_since_midnight()

                if self._active_day < _today:
                    print("current minute is %d - it's midnight" % self._current_minute)
                    #midnight!
                    self.save('track-log-%d.json' % self._active_day)
                    self.clear()

                self._active_day = _today

                self._current_minute = track_common.minutes_since_midnight()

                self._user_is_active = True

                self._idle_current = int(desktop_usage_info.idle.getIdleSec())
                _app_info = desktop_usage_info.applicationinfo.get_active_window_information()

                self._current_app_title = _app_info["TITLE"]
                if "COMMAND" in _app_info:
                    self._current_process_exe = _app_info["COMMAND"]
                else:
                    self._current_process_exe = "Process not found"

                self._rules.highlight_string(self._current_app_title)

                if self._idle_current > 10:
                    self._user_is_active = False
                    return

                _app = track_common.app_info(self._current_app_title,
                                self._current_process_exe)
                _app._category = self._rules.get_first_matching_key(_app)

                _app = self._applications.update(
                            self._current_minute,
                            _app)

            except desktop_usage_info.WindowInformationError:
                pass
            except desktop_usage_info.ToolError as ex:
                log.error(ex)

    #def info(self, minute):
        #return self._applications.info(minute)

    #def begin_index(self):
        #return self._applications.begin_index()

    #def start_time(self):
        #_s = self._applications.begin_index()
        #return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    #def now(self):
        #_s = self._current_minute
        #return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    #def is_active(self, minute):
        #return self._applications.is_active(minute)

    #def is_private(self, minute):
        #return self._applications.is_private(minute)

    #def get_time_total(self):
        #return self._current_minute - self._applications.begin_index() + 1

    #def get_time_active(self):
        #return len(self._applications._minutes)

    #def get_time_idle(self):
        #return self.get_time_total() - len(self._applications._minutes)

    #def get_time_in_category(self, category):
        #r = 0
        #for i, m in self._applications._minutes.items():
            #r += 1 if m._category == category else 0
        #return r

    #def get_max_minute(self):
        #return self._applications.end_index()

    def get_current_data(self):
        return {'minute': self._current_minute,
                'time_total':
                    self._current_minute - self._applications.begin_index() + 1,

                'user_idle': self._idle_current,
                'user_active': self._user_is_active,

                'app_title': self._current_app_title,
                'process_name': self._current_process_exe,}
