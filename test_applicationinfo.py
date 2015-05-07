#!/usr/bin/env python2
# -*- coding: utf-8 -*-


from desktop_usage_info import idle
from desktop_usage_info import applicationinfo

import time

def test_application_info():
    for i in range(2):
        try:
            print(applicationinfo.get_active_window_title())
            print(applicationinfo.get_active_process_name())
        except applicationinfo.UncriticalException:
            pass
        time.sleep(1)

if __name__ == '__main__':
    test_application_info()

