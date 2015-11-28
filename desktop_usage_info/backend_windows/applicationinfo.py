#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os

from win32gui import GetWindowText, GetForegroundWindow

def _get_active_window_title():
    return GetWindowText(GetForegroundWindow())

def _get_active_process_name():
    return ""

def _get_active_window_information():
    return {
        "TITLE": get_active_window_title(),
        # "PID": ???
        # "COMMAND": ???
    }

if __name__ == '__main__':
    import time
    import sys
    print(sys.version)
    while True:
        print(get_idle_duration())
        print(get_window())
        time.sleep(1)

