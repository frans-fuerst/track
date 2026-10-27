#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


def application_root_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))
