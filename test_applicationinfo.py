#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import idle
import time
import applicationinfo


if __name__ == '__main__':
    while True:
        try:
            print(applicationinfo.get_active_window_title())
            print(applicationinfo.get_active_process_name())
        except applicationinfo.UncriticalException:
            pass
        time.sleep(1)

