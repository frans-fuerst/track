#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import subprocess
import re

import psutil

from desktop_usage_info import ToolError
from desktop_usage_info import WindowInformationError

'''
xprop -id $(xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}') | awk '/_NET_WM_PID\(CARDINAL\)/{print $NF}'
xprop -id $(xprop -root _NET_ACTIVE_WINDOW | cut -f5 -d' ')
'''


# http://thp.io/2007/09/x11-idle-time-and-focused-window-in.html

def _get_stdout(command):
    """ run a command and return stdout
    """
    _p = subprocess.Popen(
                args=command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,)
    _stdout, _stderr = _p.communicate()
    _stdout = _stdout.decode('utf-8', errors='replace').split('\n')
    _stderr = _stderr.decode('utf-8', errors='replace').split('\n')
    if _p.returncode is not 0:
        raise WindowInformationError(
            'command "%s" did not return properly' % ' '.join(command)
            + "\n"
            + "output was: \n"
            + '\n'.join(_stdout)
            + '\n'.join(_stderr))
    return _stdout


def get_active_window_information():
    try:
        _xprop = _get_stdout(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    except:
        raise ToolError('Could not run "xprop". Is this an X-Session?')

    _id_w = None
    for line in _xprop:
        m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
        if m is not None:
            _window_id = m.group(1)

    if _window_id is None:
        raise ToolError('"xprop" did not give us _NET_ACTIVE_WINDOW.')

    try:
        _id_w = _get_stdout(['xprop', '-id', _window_id, 'WM_NAME', '_NET_WM_NAME', '_NET_WM_PID'])
    except WindowInformationError as ex:
        print(repr(ex))
        raise WindowInformationError(
            '"xprop" (ran order to get WM_NAME, _NET_WM_NAME and_NET_WM_PID) "'
            '"returned with error')
    except Exception  as ex:
        print(repr(ex))
        raise ToolError(
            'Could not run "xprop" in order to get WM_NAME, _NET_WM_NAME and_NET_WM_PID')

    _result = {}

    for line in _id_w:
        _match = re.match(".*WM_NAME\(\w+\) = (?P<name>.+)$", line)
        if _match is not None:
            _entry = _match.group("name").strip('"').strip()
            if _entry == "":
                print("could not read title from '%s'" % line)
                raise WindowInformationError('could not read app title')
            _result['TITLE'] = _entry

        _match = re.match(".*_NET_WM_PID\(\w+\) = (?P<name>.+)$", line)
        if _match is not None:
            _entry = _match.group("name").strip('"').strip()
            if _entry != "":
                _result['PID'] = int(_entry)

    if 'PID' in _result:
        process = psutil.Process(_result['PID'])
        try:
            #  # in psutil 2+ cmdline is a getter
            _result['COMMAND'] = ' '.join(process.cmdline())
        except TypeError:
            _result['COMMAND'] = ' '.join(process.cmdline)

    return _result

def _get_active_window_title():
    ''' deprecated '''
    try:
        _xprop = _get_stdout(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
        _id_w = None
        for line in _xprop:
            m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
            if m is not None:
                id_ = m.group(1)
                _id_w = _get_stdout(['xprop', '-id', id_, 'WM_NAME', '_NET_WM_NAME'])
                # _id_w = _get_stdout(['xprop', '-id', id_])
                break

        if _id_w is not None:
            for line in _id_w:
                match = re.match(".*WM_NAME\(\w+\) = (?P<name>.+)$", line)
                if match != None:
                    _result = match.group("name").strip('"')
                    if _result.strip() == "":
                        pass
                    return _result
    except Exception as e:
        logging.warn("got exception: %s" % str(e))
    return "Active window not found"


def _get_active_process_name():
    import wnck
    ''' deprecated '''
    try:
        # http://askubuntu.com/questions/152191
        screen = wnck.screen_get_default()
        # print screen
        window = screen.get_active_window()
        # print window
        pid = window.get_pid()
        process = psutil.Process(pid)
        # print(pid)
        # print(process.name)
        # print(process.exe)
        # print(process.cmdline)
        # print('strange: process.cmdline is of type "%s"' % type(process.cmdline))
        try:
            #  # in psutil 2+ cmdline is a getter
            return ' '.join(process.cmdline())
        except TypeError:
            return ' '.join(process.cmdline)
        except Exception:
            return "error in get_active_process_name(%s)" % str(pid)
    except (psutil.NoSuchProcess, AttributeError) as e:
        # print e
        raise WindowInformationError()

