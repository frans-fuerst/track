#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple

VersionInfo = namedtuple("VersionInfo", ["major", "minor", "micro", "patch"])
version_info = VersionInfo(major=0, minor=2, micro=0, patch=0)  # keep in sync with pyproject

# imports below depend on version_info being defined first
from . import errors, util  # noqa: E402
from .active_applications import ActiveApplications  # noqa: E402
from .common import (  # noqa: E402
    AppInfo,
    Category,
    Minute,
    mins_to_dur,
    secs_to_dur,
    today_int,
)
from .time_tracker import TimeTracker  # noqa: E402
from .util import catch, exception_to_string, log  # noqa: E402
