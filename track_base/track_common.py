#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from datetime import datetime
import time
import logging
from collections import namedtuple
import traceback

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

class app_info():

    def __init__(self, windowtitle="", cmdline=""):
        self._wndtitle = windowtitle
        self._cmdline = cmdline
        self._category = 0
        self._count = 0

    def __eq__(self, other):
        if not self._wndtitle == other._wndtitle:
            return False
        if not self._cmdline == other._cmdline:
            return False
        if not self._category == other._category:
            return False
        if not self._count == other._count:
            return False
        return True

    def generate_identifier(self):
        return self._wndtitle

    def __hash__(self):
        x = hash((self._wndtitle, self._cmdline))
        return x

    def __str__(self):
        return "%s - [%s %d]" % (self._wndtitle, self._category, self._count)

    def load(self, data):
        try:
            self._wndtitle, self._category, self._count, self._cmdline = data
        except:
            print('tried to expand %s to (title, category, count, cmdline)' % (
                  str(data)))
            raise Exception('could not load app_info data')
        return self

    def __data__(self):  # const
        return (self._wndtitle, self._category, self._count, self._cmdline)

    def get_category(self):
        return self._category

    def set_new_category(self, new_category):
        self._category=new_category

    def get_count(self):
        return self._count

class minute():
    """ a minute holds a category and a list of apps
    """
    def __init__(self, category=0, apps=None):
        self._category = 0
        if apps is None:
            self._apps = {}
        else:
            self._apps = apps  # app_info -> count

    def __eq__(self, other):
        if not self._category == other._category:
            return False
        if not self._apps == other._apps:
            for a, c in self._apps.items():
                print("s: %s:'%s' - %d" % (hex(id(a)), a, c))
            for a, c in other._apps.items():
                print("o: %s - %d" % (a, c))
            return False
        return True

    def dump(self):
        print("category %d" % self._category)

    def init(self, data):
        self._category, self._apps = data
        return self

    def _rebuild(self):
        if len(self._apps) == 0:
            return 0  # todo: need undefined

        _categories = {} # category -> sum
        for a, c in self._apps.items():
            try:
                if a._category not in _categories:
                    _categories[a._category] = c
                else:
                    _categories[a._category] += c
            except:
                pass

        self._category = _categories.keys()[
                                _categories.values().index(
                                    max(_categories.values()))]
        # print(self._category)

    def add(self, app_instance):
        if app_instance not in self._apps:
            self._apps[app_instance] = 1
        else:
            self._apps[app_instance] += 1
        self._rebuild()

    def get_main_app(self):
        _a = max(self._apps, key=lambda x: self._apps[x])
        return _a._wndtitle

    def rebuild_categories(self, get_category):
        for a, c in self._apps.items():
            a.set_new_category(get_category(a))
        self._rebuild()

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

import threading
class frame_grabber:
    stacks = {}
    def __init__(self, logger, extra=None):
        self.n = traceback.extract_stack()[-2][2]
        self.e = extra
        self.l = logger
        t = threading.current_thread()
        if not t in frame_grabber.stacks:
            frame_grabber.stacks[t] = (len(frame_grabber.stacks) * 10, [])
        self.s = frame_grabber.stacks[t]
        self.prefix = "T%d %s" % (self.s[0], " " * 4 * len(self.s[1]))
        self.postfix = "%s() %s" % (self.n, "(%s)" % self.e if self.e else "")

    def __enter__(self):
        self.s[1].append(self.n)
        self.l.debug('>> %s enter %s', self.prefix, self.postfix)
        return self

    def __exit__(self, *args):
        self.l.debug('<< %s leave %s', self.prefix, self.postfix)
        self.s[1].pop()
        return
