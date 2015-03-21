#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from datetime import datetime

import idle
import applicationinfo

def seconds_since_midnight():
    now = datetime.now()
    return int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())


def minutes_since_midnight():
    #return int(seconds_since_midnight() / 5)
    return int(seconds_since_midnight() / 60)


class time_tracker():

    def __init__(self):
        self._start_minute = minutes_since_midnight()
        self._minutes = {}
        self._max_minute = 0
        self._idle = 0
        self._current_app_title = ""
        self._current_process_exe = ""
        self._user_is_active = True
        
    def update(self):
   
        self._idle = idle.getIdleSec()
        self._current_app_title = applicationinfo.get_active_window_title() 
        self._current_process_exe = applicationinfo.get_active_process_name()
        
        _minute_index = minutes_since_midnight()

        self._max_minute = _minute_index

        if self._idle > 5:
            self._user_is_active = False
            return
        self._user_is_active = True
        
        if _minute_index not in self._minutes:
            self._minutes[_minute_index] = []
        self._minutes[_minute_index].append(self._current_app_title)

    def first_index(self):
        return self._start_minute

    def is_active(self, minute):
        if minute in self._minutes:
            return True
        return False

    def get_active_time(self):
        _result = ""
        _minutes = len(self._minutes)
        if _minutes >= 60:
            _result = str(int(_minutes / 60))+"h "
            _minutes %= 60
        _result += str(_minutes ) + "m"
        return _result

    def get_current_minute(self):
        return self._max_minute

    def get_idle(self):
        return self._idle
        
    def get_current_app_title(self):
        return self._current_app_title
        
    def get_current_process_name(self):
        return self._current_process_exe
        
    def user_is_active(self):
        return self._user_is_active

if __name__ == '__main__':
    print('this is the timetracker core module. run track.py')

