#!/usr/bin/env python2
# -*- coding: utf-8 -*-


from desktop_usage_info import idle
from desktop_usage_info import applicationinfo

import time

def test_application_info():
    for i in range(2):
        info = applicationinfo.get_active_window_information()
        assert "PID" in info
        print("PID:     ", info["PID"])

        assert "TITLE" in info
        print("TITLE:   ", info["TITLE"])

        assert "COMMAND" in info
        print("COMMAND: ", info["COMMAND"])

        time.sleep(1)

if __name__ == '__main__':
    test_application_info()

