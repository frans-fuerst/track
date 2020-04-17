#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""All the stuff needed by several components
"""

from datetime import datetime
import time
import os
import logging
from collections import namedtuple, Counter
import traceback
import operator
from enum import IntEnum

class Category(IntEnum):
    IDLE = 0
    UNASSIGNED = 1
    WORK = 2
    PRIVATE = 3
    BREAK = 4


class track_error(Exception):
    pass

class path_exists_error(track_error):
    pass

class file_not_found_error(track_error):
    pass

class read_permission_error(track_error):
    pass

class not_connected(track_error):
    pass

class protocol_error(track_error):
    pass


def mins_to_date(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = "%2d:" %(_minutes / 60)
        _minutes %= 60
    _result += "%02d" % _minutes
    return _result

def secs_to_dur(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"m "
        _minutes %= 60
    _result += str(_minutes ) + "s"
    return _result


def mins_to_dur(mins):
    return "%d:%02d" % (mins / 60, mins % 60) if mins >= 60 else "%dm" % mins

    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60)) + "h "
        _minutes %= 60
        _result += "%02d" % _minutes + "m"
    else:
        _result += "%d" % _minutes + "m"
    return _result


def today_str():
    return datetime.fromtimestamp(time.time()).strftime('%Y%m%d')


def today_int():
    now = datetime.now()
    return now.year * 10000 + now.month * 100 + now.day


def seconds_since_midnight():
    now = datetime.now()
    return int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())


def minutes_since_midnight():
    #return int(seconds_since_midnight() / 2)
    return int(seconds_since_midnight() / 60)


class AppInfo:
    def __init__(self, windowtitle="", cmdline=""):
        self._wndtitle = windowtitle
        self._cmdline = cmdline
        self._category = 0
        self._count = 0

    def __eq__(self, other) -> bool:
        return (self._wndtitle == other._wndtitle and
                self._cmdline == other._cmdline and
                self._category == other._category)

    def generate_identifier(self):
        return self._wndtitle

    def __hash__(self):
        return hash((self._wndtitle, self._cmdline))

    def __str__(self):
        return "%s - [cat: %s, count: %d]" % (self._wndtitle, self._category, self._count)

    def load(self, data):
        try:
            self._wndtitle, self._category, self._count, self._cmdline = data
        except:
            print('tried to expand %s to (title, category, count, cmdline)' % (
                  str(data)))
            raise Exception('could not load AppInfo data')
        return self

    def __data__(self):  # const
        return (self._wndtitle, self._category, self._count, self._cmdline)

    def get_category(self):
        return self._category

    def set_new_category(self, new_category):
        self._category=new_category

    def get_count(self):
        return self._count


class Minute:
    """ a minute holds a category and a list of apps
    """
    def __init__(self, app_counter=None):
        self._app_counter = app_counter or {}

    def __eq__(self, other):
        if not self._app_counter == other._app_counter:
            for a, c in self._app_counter.items():
                print("s: %s:'%s' - %d" % (hex(id(a)), a, c))
            for a, c in other._app_counter.items():
                print("o: %s - %d" % (a, c))
            return False
        return True

    def main_category(self):
        # app1(2): 5
        # app2(1): 2
        # app3(1): 7
        # 2: 5, 1: 2, 1: 7
        # 2: 5, 1: 9
        return self.main_app()._category

    def add(self, app_instance):
        self._app_counter[app_instance] = self._app_counter.get(app_instance, 0) + 1

    def main_app(self):
        return max(self._app_counter, key=lambda x: self._app_counter[x])


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        format="%(asctime)s %(name)17s %(levelname)s:  %(message)s",
        datefmt="%y%m%d-%H%M%S",
        level=level)
    logging.addLevelName(logging.CRITICAL, "CC")
    logging.addLevelName(logging.ERROR,    "EE")
    logging.addLevelName(logging.WARNING,  "WW")
    logging.addLevelName(logging.INFO,     "II")
    logging.addLevelName(logging.DEBUG,    "DD")
    logging.addLevelName(logging.NOTSET,   "NA")


def fopen(filename, mode='r', buffering=1):
    try:
        return open(filename, mode, buffering)
    except IOError as ex:
        if ex.errno == 2:
            raise file_not_found_error()
        elif ex.errno == 13:
            raise read_permission_error()
        raise

def make_dirs(path):
    try:
        os.makedirs(os.path.expanduser(path))
    except OSError as ex:
        if ex.errno == 17:
            raise path_exists_error()
        raise
