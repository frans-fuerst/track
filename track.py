#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import sys
import signal
import logging

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
        self._tracker.update()
        _idle = self._tracker.get_idle()
        _app = self._tracker.get_current_app_title()
    
        self.lbl_idle.setText(str(_idle))
        self.lbl_active.setText(str(self._tracker.get_active_time()))
        self.lbl_title.setText(self._tracker.get_current_app_title())
        self.lbl_process.setText(self._tracker.get_current_process_name())
        self.lbl_start_time.setText(self._tracker.start_time())
        
        p = self.lbl_idle.palette()
        if self._tracker.user_is_active():
            p.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.green)
        else:
            p.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.gray)
        self.lbl_idle.setPalette(p)
        
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
    
