#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
import logging 

from desktop_usage_info import idle
from desktop_usage_info import applicationinfo

import track_base
import track_common

class time_tracker():
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
        

        # -- persist
        self._applications = track_base.active_applications()
        self._rules = track_base.rules_model()

        #self._rules.modified_rules.connect(self.update_categories)

    def __eq__(self, other):
        return False

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def load(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % track_common.today_str()
        # print(_file_name)
        try:
            with open(_file_name) as _file:
                _struct = json.load(_file)
        except IOError:
            if filename is not None:
                logging.warn('file "%s" does not exist' % filename)
            return

        self._applications.from_dict(_struct)

    def save(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % track_common.today_str() 
        # print(_file_name)
        _app_data = self._applications.__data__()
        with open(_file_name, 'w') as _file:
            json.dump(_app_data, _file,
                      sort_keys=True) #, indent=4, separators=(',', ': '))
            
        _test_model = track_base.active_applications(None)
        _test_model.from_dict(_app_data)
        assert self._applications == _test_model

    def get_applications_model(self):
        return self._applications

    def get_rules_model(self):
        return self._rules

    def update(self):
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

            self._idle_current = idle.getIdleSec()
            self._current_app_title = applicationinfo.get_active_window_title()
            try:
                self._current_process_exe = applicationinfo.get_active_process_name()
            except applicationinfo.UncriticalException as e: #necessary to run in i3
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

        except applicationinfo.UncriticalException as e:
            pass

    def info(self, minute):
        return self._applications.info(minute)

    def begin_index(self):
        return self._applications.begin_index()
    
    def start_time(self):
        _s = self._applications.begin_index()
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def now(self):
        _s = self._current_minute
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def is_active(self, minute):
        return self._applications.is_active(minute)

    def is_private(self, minute):
        return self._applications.is_private(minute)

    #def get_time_total(self):
        #return self._current_minute - self._applications.begin_index() + 1

    def get_time_active(self):
        return len(self._applications._minutes)

    def get_time_idle(self):
        return self.get_time_total() - len(self._applications._minutes)

    def get_time_in_category(self, category):
        r = 0
        for i, m in self._applications._minutes.items():
            r += 1 if m._category == category else 0
        return r

    def get_max_minute(self):
        return self._tracker.end_index()

    def get_current_data(self):
        return {'minute': self._current_minute,
                'time_total': 
                    self._current_minute - self._applications.begin_index() + 1,

                'user_idle': self._idle_current,
                'user_active': self._user_is_active,
                
                'app_title': self._current_app_title,
                'process_name': self._current_process_exe,}
    '''
    def get_current_minute(self):
        return self._current_minute

    def get_idle(self):
        return self._idle_current

    def get_current_app_title(self):
        return self._current_app_title

    def get_current_process_name(self):
        return self._current_process_exe

    def user_is_active(self):
        return self._user_is_active
    '''
    
    # def update_categories(self):
    #    self._applications.update_all_categories(self._rules.get_first_matching_key)

    #def new_regex_rule(self):
    #    self._rules.add_rule()
