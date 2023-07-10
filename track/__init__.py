#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


def application_root_dir():
    return os.path.dirname(__file__[max(0, __file__.rfind(":")) :])
