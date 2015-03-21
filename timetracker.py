#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from datetime import datetime


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
        
    def update(self, idle, active_title):
        _minute_index = minutes_since_midnight()

        self._max_minute = _minute_index

        if idle > 5:
            return

        if _minute_index not in self._minutes:
            self._minutes[_minute_index] = []
        self._minutes[_minute_index].append(active_title)

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

