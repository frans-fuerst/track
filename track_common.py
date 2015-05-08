#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from datetime import datetime
import time


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

