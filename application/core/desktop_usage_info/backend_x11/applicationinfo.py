#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import re

import psutil

from .. import ToolError
from .. import WindowInformationError

# xprop -id $(xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}') | awk '/_NET_WM_PID\(CARDINAL\)/{print $NF}'
# xprop -id $(xprop -root _NET_ACTIVE_WINDOW | cut -f5 -d' ')


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
    if _p.returncode != 0:
        raise WindowInformationError(
            'command "%s" did not return properly' % ' '.join(command) +
            "\n" +
            "output was: \n" +
            '\n'.join(_stdout) +
            '\n'.join(_stderr))
    return _stdout


def get_active_window_information():
    try:
        _xprop = _get_stdout(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    except:
        raise ToolError('Could not run "xprop". Is this an X-Session?')

    _id_w = None
    for line in _xprop:
        m = re.search(r"^_NET_ACTIVE_WINDOW.* ([\w]+)$", line)
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
    except Exception as ex:
        print(repr(ex))
        raise ToolError(
            'Could not run "xprop" in order to get WM_NAME, _NET_WM_NAME and_NET_WM_PID')

    _result = {}

    for line in _id_w:
        _match = re.match(r".*WM_NAME\(\w+\) = (?P<name>.+)$", line)
        if _match is not None:
            _entry = _match.group("name").strip('"').strip()
            if _entry == "":
                print("could not read title from '%s'" % line)
                raise WindowInformationError('could not read app title')
            _result['TITLE'] = _entry

        _match = re.match(r".*_NET_WM_PID\(\w+\) = (?P<name>.+)$", line)
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
