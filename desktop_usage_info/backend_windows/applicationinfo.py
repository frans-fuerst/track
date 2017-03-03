#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from win32gui import GetWindowText, GetForegroundWindow

def _get_active_window_title() -> str:
    return GetWindowText(GetForegroundWindow())

def _get_active_process_name() -> str:
    return ""

def get_active_window_information() -> dict:
    return {
        "TITLE": _get_active_window_title(),
        # "PID": ???
        # "COMMAND": ???
    }

if __name__ == '__main__':
    import time
    import sys
    print(sys.version)
    while True:
        print(get_active_window_information())
        time.sleep(1)

