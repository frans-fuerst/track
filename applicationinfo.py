#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import subprocess
import re

import wnck
import psutil


class UncriticalException(Exception):
    pass

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

    try:
        _xprop = get_stdout(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
        _id_w = None
        for line in _xprop:
            m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
            if m is not None:
                id_ = m.group(1)
                _id_w = get_stdout(['xprop', '-id', id_, 'WM_NAME'])
                # _id_w = get_stdout(['xprop', '-id', id_])
                break
    
        if _id_w is not None:
    
            for line in _id_w:
                match = re.match("WM_NAME\(\w+\) = (?P<name>.+)$", line)
                if match != None:
                    return match.group("name").decode().strip('"')
    except Exception as e:
        logging.warn("got exception: %s" % str(e))
    return "Active window not found"


def get_active_process_name():
    try:
        # http://askubuntu.com/questions/152191
        screen = wnck.screen_get_default()
        window = screen.get_active_window()
        pid = window.get_pid()
        process = psutil.Process(pid)
        # print(pid)
        # print(process.name)
        # print(process.exe)
        # print(process.cmdline)
        return ' '.join(process.cmdline)
    except AttributeError as e:
        raise UncriticalException()        

