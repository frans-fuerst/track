#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import subprocess
import re

# http://thp.io/2007/09/x11-idle-time-and-focused-window-in.html

def get_stdout(command):
    """ run a command and return stdout 
    """
    _p = subprocess.Popen(
                args=command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,)
    _stdout, _stderr =_p.communicate()
    if _p.returncode is not 0:
        raise Exception('command "%s" did not return properly' % ' '.join(command))
    return _stdout.split('\n')

def get_active_window_title():

    _xprop = get_stdout(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    _id_w = None
    for line in _xprop:
        m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
        if m is not None:
            id_ = m.group(1)
            _id_w = get_stdout(['xprop', '-id', id_, 'WM_NAME'])
            _id_w = get_stdout(['xprop', '-id', id_])
            break
#    print(_id_w)
    if _id_w is not None:
        for line in _id_w:
            if '/bin' in line:
                print(line)

        for line in _id_w:
            match = re.match("WM_NAME\(\w+\) = (?P<name>.+)$", line)
            if match != None:
                return match.group("name")

    return "Active window not found"

