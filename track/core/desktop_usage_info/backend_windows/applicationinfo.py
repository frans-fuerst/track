#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Retrieve desktop usage info - Windows version"""

from win32gui import GetWindowText, GetForegroundWindow

def _get_active_window_title():
    return GetWindowText(GetForegroundWindow())

def _get_active_process_name():
    return ""

def get_active_window_information():
    return {
        "TITLE": _get_active_window_title(),
        # "PID": ???
        # "COMMAND": ???
    }
