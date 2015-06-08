#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import json
import re
import track_qt
import track_common

def test_active_applications():
    aa = track_qt.active_applications(None)

def test_import():
    a = track_qt.active_applications(None)
    _total_dur = 0
    _count = 0
    _lunch_time = 12 * 60 + 50
    for root, dirs, files in os.walk('.'):
        for _f in [f for f in sorted(files) if f.endswith('.json')]:
            _file = os.path.join(root, _f)
            c = json.load(open(_file))
            try:
                a.from_dict(c)
            except:
                print('ERROR: could not load "%s"' % _file)
                continue
            _end = a.end_index()
            _begin = a.begin_index()
            _dur = _end - _begin

            (_b, _e), _a = a.info(_lunch_time)
            _lunch_dur = _e - _b
            if not (_e - _b >= 30 and _a == 'idle'):
                _lunch_dur = 0
                print("WARNING: no lunch time found for %s" % _file)
            _dur -= _lunch_dur
            if _dur > 300:
                _total_dur += _dur
                _count += 1
            else:
                print('WARNING: ignore "%s" - less than 5h tracked' % _file)

            print("f: %23s, count: %3d, begin: %s (%4d), end: %s (%4d), lunch: %7s, dur: %7s" % (
                _file, a.rowCount(), 
                track_common.mins_to_date(_begin), _begin, 
                track_common.mins_to_date(_end), _end, 
                track_common.mins_to_dur(_lunch_dur),
                track_common.mins_to_dur(_dur)))
            # print(re.search('track-.*.json', _file) is not None)
    print(track_common.mins_to_dur(_total_dur / _count))

if __name__ == '__main__':
    test_active_applications()
    test_import()
            

