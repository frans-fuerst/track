#!/usr/bin/env python3
"""System test: needs a running X session with a focused window"""

import time

import pytest

from track.core.desktop_usage_info import applicationinfo

pytestmark = pytest.mark.system


def test_application_info():
    for _ in range(2):
        info = applicationinfo.get_active_window_information()
        assert "TITLE" in info
        assert "PID" in info
        assert "COMMAND" in info
        time.sleep(1)
