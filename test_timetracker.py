#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import json
import re
import timetracker
import track_common

def test_import():
    a = timetracker.active_applications(None)
    _total_dur = 0
    _count = 0
    for root, dirs, files in os.walk('.'):
        for _file in [f for f in sorted(files) if f.endswith('.json')]:
            c = json.load(open(_file))
            try:
                a.from_dict(c)
            except:
                print('ERROR: could not load "%s"' % _file)
                continue
            _end = a.end_index()
            _begin = a.begin_index()
            _dur = _end - _begin
            if _dur > 300:
                _total_dur += _dur
                _count += 1
            else:
                print('WARNING: ignore "%s" - less than 5h tracked' % _file)

            print("f: %s, count: %3d, begin: %s (%4d), end: %s (%4d), dur: %s" % (
                _file, a.rowCount(), 
                track_common.mins_to_date(_begin), _begin, 
                track_common.mins_to_date(_end), _end, 
                track_common.mins_to_dur(_dur)))
            # print(re.search('track-.*.json', _file) is not None)
    print(track_common.mins_to_dur(_total_dur / _count))
if __name__ == '__main__':
    test_import()
            

