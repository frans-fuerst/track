#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""All the stuff needed by several components
"""

import os
import sys
from datetime import datetime
import time
import argparse
import re
from enum import IntEnum
from typing import Any, Dict, Sequence, Tuple  # pylint: disable=unused-import

from .util import log
from . import version_info


class Category(IntEnum):
    """One of each currently known time categories"""
    IDLE = 0
    UNASSIGNED = 1
    WORK = 2
    PRIVATE = 3
    BREAK = 4


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

    #def category(self):
        #return self._category

    def set_category(self, category):
        self._category = category

    def set_new_category(self, new_category):
        self._category = new_category

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


Rule = Tuple[str, Category]
Rules = Sequence[Rule]


def get_category(app: AppInfo, rules: Rules) -> Category:
    """Maps an Application to a track category"""
    app_string_representation = app.generate_identifier()
    for rule, category in rules:
        if re.search(rule, app_string_representation, flags=re.IGNORECASE):
            return category
    return Category.UNASSIGNED


def recategorize(apps: Sequence[AppInfo], rules: Rules) -> None:
    for app in apps:
        app.set_category(get_category(app, rules))


def mins_to_date(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = "%2d:" % (_minutes / 60)
        _minutes %= 60
    _result += "%02d" % _minutes
    return _result


def secs_to_dur(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"m "
        _minutes %= 60
    _result += str(_minutes) + "s"
    return _result


def mins_to_dur(mins: int) -> str:
    return "%d:%02d" % (mins / 60, mins % 60) if mins >= 60 else "%dm" % mins


def today_str():
    return datetime.fromtimestamp(time.time()).strftime('%Y%m%d')


def today_int():
    now = datetime.now()
    return now.year * 10000 + now.month * 100 + now.day


def seconds_since_midnight():
    now = datetime.now()
    return int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())


def minutes_since_midnight():
    return int(seconds_since_midnight() / 60)


def setup_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Set some default arguments for track components"""
    parser.add_argument('--log-level',
                        '-l',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
                        default='INFO',)
    parser.add_argument('--data-dir',
                        '-d',
                        default=os.path.expanduser('~/.track'),)
    parser.add_argument('--port', type=int, default=3456, help='IPv4 port to connect to')


def log_system_info(args) -> None:
    """Print some interestion system information used for problem solving"""
    log().info("Used Python interpreter: v%s (%s)",
               '.'.join((str(e) for e in sys.version_info)), sys.executable)
    log().info("App version:  %s", str(version_info))
    log().info("Track dir:  %s", args.data_dir)
