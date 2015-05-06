#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import json

import timetracker

if __name__ == '__main__':
    a = timetracker.active_applications(None)
    for root, dirs, files in os.walk('.'):
        for _file in [f for f in files if f.endswith('.json')]:
            c = json.load(open(_file))
            a.from_dict(c)
            print(_file, len(c), a.rowCount(), a.begin_index(), a.end_index())
            

