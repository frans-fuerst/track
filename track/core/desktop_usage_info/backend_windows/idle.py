#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os

if os.name == "nt":

    from ctypes import Structure, byref, c_uint, sizeof, windll

    class LASTINPUTINFO(Structure):
        _fields_ = [
            ("cbSize", c_uint),
            ("dwTime", c_uint),
        ]

    def getIdleSec() -> int:
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = sizeof(lastInputInfo)
        windll.user32.GetLastInputInfo(byref(lastInputInfo))
        millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return int(millis / 1000.0)
