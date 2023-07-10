#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple

version_info = namedtuple("version_info", ["major", "minor", "micro", "patch"])
version_info = version_info(major=2020, minor=5, micro=8, patch=0)

from . import errors, util
from .active_applications import ActiveApplications
from .common import AppInfo, Category, Minute, mins_to_dur, secs_to_dur, today_int
from .time_tracker import TimeTracker
from .util import catch, exception_to_string, log
