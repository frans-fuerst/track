#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import sys
import signal
import logging

import timetracker

def mins_to_str(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"h "
        _minutes %= 60
    _result += str(_minutes ) + "m"
    return _result

class track_ui(QtGui.QMainWindow):

    def __init__(self):
        super(track_ui, self).__init__()
        self._tracker = timetracker.time_tracker(self)
        
        self.initUI()
        self.frm_timegraph.setTracker(self._tracker)
        self.tbl_active_applications.setModel(self._tracker.get_applications_model())
        
        self.tbl_active_applications.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

        self.tbl_active_applications.setColumnWidth(0, self.tbl_active_applications.width() * 0.7)
        self.tbl_active_applications.setColumnWidth(1, self.tbl_active_applications.width() * 0.1)
        
        self.show()
        
    def initUI(self):      
        uic.loadUi('track.ui', self)
        
        self.setGeometry(300, 300, 700, 500)
        self.setWindowTitle('Track')
        # self.lbl_color_work.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.cyan)

        _idle_timer = QtCore.QTimer(self)
        _idle_timer.timeout.connect(self.update_idle)
        self.pb_save.clicked.connect(self.pb_save_clicked)
        _idle_timer.start(1000)

    def pb_save_clicked(self):
        print("save")
        self._tracker.save()

    def update_idle(self):
        self._tracker.update()
        _idle = self._tracker.get_idle()
        _app = self._tracker.get_current_app_title()
    
        try:
            self.lbl_idle.setText(str(_idle))
            #self.lbl_private.setText(str(self._tracker.get_private_time()))
            self.lbl_title.setText(self._tracker.get_current_app_title())
            self.lbl_process.setText(self._tracker.get_current_process_name())

            # now-begin, active (.x) work (.x)
            _time_total = self._tracker.get_time_total()
            _time_active = self._tracker.get_time_active()
            _time_work = self._tracker.get_time_work()
            _time_private = self._tracker.get_time_private()
            _time_idle = self._tracker.get_time_idle()

            self.lbl_times.setText(
                "T: %s  A: %s (%.1f)  W: %s (%.1f)  "
                "P: %s (%.1f)  I: %s (%.1f)" %
                (mins_to_str(_time_total),
                 mins_to_str(_time_active), _time_active / float(_time_total), 
                 mins_to_str(_time_work), _time_work / float(_time_total),
                 mins_to_str(_time_private), _time_private / float(_time_total),
                 mins_to_str(_time_idle), _time_idle / float(_time_total)))


            self.lbl_start_time.setText("%s - %s" % (
                 self._tracker.start_time(), self._tracker.now()))
        except Exception as e:
            logging.error(e)

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
    
