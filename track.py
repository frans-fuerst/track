#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import sys
import random
import signal
import logging
import subprocess
import re

import idle

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


class track_ui(QtGui.QWidget):

    def __init__(self):
        super(track_ui, self).__init__()
        print('init')
        self.show()

        self.initUI()
        
    def initUI(self):      

        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Points')

        _idle_timer = QtCore.QTimer(self)
        _idle_timer.timeout.connect(self.update_idle)
        _idle_timer.start(1000)

        print(dir(QtCore.QTimer))
        self.show()
    
    def update_idle(self):
        print("update idle: %d, avive window: %s" % (idle.getIdleSec(), get_active_window_title()))

    def paintEvent(self, e):

        print('paint')
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def drawPoints(self, qp):
      
        qp.setPen(QtCore.Qt.red)
        size = self.size()
        
        for i in range(1000):
            qp.drawLine(i, 100, i, 200)   

    def system_signal(self, s):
        sig_name = "unknown"
        if s == signal.SIGABRT:
            sig_name = "SIGABRT"
        if s == signal.SIGINT:
            sig_name = "SIGINT"
        if s == signal.SIGSEGV:
            sig_name = "SIGSEGV"
        if s == signal.SIGTERM:
            sig_name = "SIGTERM"
        logging.info("got signal %s (%s)", sig_name, str(s))
        self.close()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = track_ui()
    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(s, lambda signal, frame: ex.system_signal(signal))
    sys.exit(app.exec_())
