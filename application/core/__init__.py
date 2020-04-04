#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple

version_info = namedtuple('version_info', ['major', 'minor', 'micro', 'patch'])
version_info = version_info(major=2020, minor=4, micro=17, patch=0)

from . import util
from . import errors
from .util import (
    catch,
    log,
    exception_to_string,
    )

from .common import (
    Category,
    Minute,
    AppInfo,
    mins_to_dur,
    secs_to_dur,
    today_int,
)
from .active_applications import ActiveApplications
from .time_tracker import TimeTracker
