#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import sys
import signal
import logging

import idle
import applicationinfo
import timetracker


class track_ui(QtGui.QMainWindow):

    def __init__(self):
        super(track_ui, self).__init__()
        self._tracker = timetracker.time_tracker()
        
        self.initUI()
        self.frm_timegraph.setTracker(self._tracker)
        self.show()
        
    def initUI(self):      
        uic.loadUi('track.ui', self)
        
        self.setGeometry(300, 300, 700, 300)
        self.setWindowTitle('Track')

        _idle_timer = QtCore.QTimer(self)
        _idle_timer.timeout.connect(self.update_idle)
        _idle_timer.start(1000)

    
    def update_idle(self):
        _idle = idle.getIdleSec()
        _app = applicationinfo.get_active_window_title() 
        self.lbl_idle.setText(str(_idle))
        self.lbl_active.setText(str(self._tracker.get_active_time()))
        print("update idle: %d, avive window: %s" % (_idle, _app))
        self._tracker.update(_idle, _app)
        self.update()


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
