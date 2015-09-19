#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os

if os.name == 'nt':

    from win32gui import GetWindowText, GetForegroundWindow


    class UncriticalException(Exception):
        pass


    def get_active_window_title():
        return GetWindowText(GetForegroundWindow())


    def get_active_process_name():
        return ""


    if __name__ == '__main__':
        import time
        import sys
        print(sys.version)
        while True:
            print(get_idle_duration())
            print(get_window())
            time.sleep(1)

