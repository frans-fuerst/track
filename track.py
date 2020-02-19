#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import signal
import argparse
import os.path
from contextlib import suppress
from typing import List

try:
    from PyQt5 import QtWidgets, QtGui, QtCore, uic
except ImportError:
    print("you have to have PyQt5 for your version of Python (%s) installed"
          % ".".join(str(x) for x in sys.version_info))
    sys.exit(-1)

import track_base
import track_qt
from util import log, show_system_info, setup_argument_parser, setup_logging


i_to_e = {getattr(QtCore.QEvent, e): e for e in dir(QtCore.QEvent)
          if isinstance(getattr(QtCore.QEvent, e), int)}

def start_server_process():
    import subprocess
    log().info('start track server daemon')
    server_file = os.path.join(os.path.dirname(__file__), 'track_server.py')
    subprocess.Popen([sys.executable, server_file])


class track_ui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self._connected = False
        self._update_timer = None
        self.tray_icon = None

        self._tracker = track_qt.time_tracker_qt(self)

        self.directory = os.path.dirname(os.path.realpath(__file__))

        self.initUI()

        self.frm_timegraph.setTracker(self._tracker)

        self.tbl_active_applications.setModel(self._tracker.get_applications_model())
        self.tbl_active_applications.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.tbl_active_applications.setColumnWidth(0, self.tbl_active_applications.width() * 0.75)
        self.tbl_active_applications.setColumnWidth(1, self.tbl_active_applications.width() * 0.1)
        self.tbl_active_applications.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tbl_active_applications.setDragEnabled(True)
        self.tbl_active_applications.setDropIndicatorShown(True)


        self.tbl_category_rules.setModel(self._tracker.get_rules_model())
        self.tbl_category_rules.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.tbl_category_rules.setColumnWidth(0, self.tbl_category_rules.width() * 0.05)
        self.tbl_category_rules.setColumnWidth(1, self.tbl_category_rules.width() * 0.65)
        self.tbl_category_rules.setColumnWidth(3, self.tbl_category_rules.width() * 0.10)

        self.tbl_category_rules.setDragEnabled(True)
        self.tbl_category_rules.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tbl_category_rules.setDropIndicatorShown(True)
        self.tbl_category_rules.viewport().setAcceptDrops(True)
        self.tbl_category_rules.setDragDropOverwriteMode(False)

    def initUI(self):
        trackui_path = os.path.join(self.directory, 'track.ui')
        uic.loadUi(trackui_path, self)

        self.setGeometry(300, 0, 700, 680)  # todo: maximize vertically
#        self.setGeometry(300, 50, 700, 680)  # todo: maximize vertically

        self.setWindowTitle('Track')
        # self.lbl_color_work.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.cyan)

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self.update_idle)
        self.pb_regex.clicked.connect(self.pb_regex_clicked)

        self.initialize_tray_icon()

    def initialize_tray_icon(self):
        style = self.style()

        # Set the window and tray icon to something
        icon = style.standardIcon(QtWidgets.QStyle.SP_MediaSeekForward)
        self.tray_icon = QtWidgets.QSystemTrayIcon()
        self.tray_icon.setIcon(QtGui.QIcon(icon))
        self.setWindowIcon(QtGui.QIcon(icon))

        # Restore the window when the tray icon is double clicked.
        self.tray_icon.activated.connect(self.restore_window)

    def _connect(self):
        _retried = False
        while True:
            try:
                log().info('connect to track server..')
                self._tracker.connect('tcp://127.0.0.1:3456')
                log().info('connected!')
                self._connected = True
                return True
            except track_qt.server_timeout:
                if _retried:
                    log().error("could not connect to track server")
                    return False
                log().info("could not connect to server - assume "
                         "it's not running and start a server instance")
                _retried = True
                start_server_process()

    def event(self, event):
        _type = event.type()
        _event_str = "'%s' (%d)" % (
            i_to_e[_type] if _type in i_to_e else "unknown", _type)
        with track_base.frame_grabber(log(), _event_str):
            if _type == QtCore.QEvent.WindowActivate and not self._connected:
                # we abuse this event as some sort of WindowShow event
                if self._connect():
                    self._update_timer.start(1000)
                else:
                    QtWidgets.QMessageBox.information(
                        self, "track service unreachable",
                        "Cannot reach the local track service even after starting "
                        "a new instance.\nPlease restart track on command "
                        "line to get some more info and file a bug!\n\nBye!",
                        buttons=QtWidgets.QMessageBox.Ok)
                    QtWidgets.QApplication.quit()
            elif _type == QtCore.QEvent.WindowStateChange and self.isMinimized():
                # The window is already minimized at this point.  AFAIK,
                # there is no hook stop a minimize event. Instead,
                # removing the Qt.Tool flag should remove the window
                # from the taskbar.
                self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.Tool)
                self.tray_icon.show()
                return True
            else:
                # log.debug("unhandled event '%s' (%d)",
                #         i_to_e[_type] if _type in i_to_e else "unknown",
                #         _type)
                pass

            return super(track_ui, self).event(event)

    def restore_window(self, reason):
        with track_base.frame_grabber(log()):

            if reason == QtGui.QSystemTrayIcon.DoubleClick:
                self.tray_icon.hide()
                # self.showNormal will restore the window even if it was
                # minimized.
                self.showNormal()

    def pb_regex_clicked(self):
        self._tracker.new_regex_rule()

    def update_idle(self):
        with track_base.frame_grabber(log()):
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
                    (track_base.mins_to_dur(_time_total),
                     track_base.mins_to_dur(_time_active), _time_active / float(_time_total),
                     track_base.mins_to_dur(_time_work), _time_work / float(_time_total),
                     track_base.mins_to_dur(_time_private), _time_private / float(_time_total),
                     track_base.mins_to_dur(_time_idle), _time_idle / float(_time_total)))

                self.lbl_start_time.setText("%s - %s" % (
                     self._tracker.start_time(), self._tracker.now()))

            except Exception as e:
                log().error(e)

            p = self.lbl_idle.palette()
            if self._tracker.user_is_active():
                p.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.green)
            else:
                p.setColor(self.lbl_idle.backgroundRole(), QtCore.Qt.gray)
            self.lbl_idle.setPalette(p)

            self.update()

    def closeEvent(self, _):
        self.cleanup()

    def cleanup(self):
        if self._tracker.initialized():
            self._tracker.save()


def sigint_handler(s, window):
    with track_base.frame_grabber(log()):
        sig_name = "unknown"
        if s == signal.SIGABRT:
            sig_name = "SIGABRT"
        if s == signal.SIGINT:
            sig_name = "SIGINT"
        if s == signal.SIGSEGV:
            sig_name = "SIGSEGV"
        if s == signal.SIGTERM:
            sig_name = "SIGTERM"
        log().info("got signal %s (%s)", sig_name, str(s))
        window.cleanup()
        QtGui.QApplication.quit()


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    setup_argument_parser(parser)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """read command line arguments, configure application and run command
    specified on command line"""
    args = parse_arguments(argv or sys.argv[1:])
    setup_logging(args)

    show_system_info()

    app = QtWidgets.QApplication(sys.argv)

    #with open(os.path.join(APP_DIR, STYLESHEET)) as f:
    #    app.setStyleSheet(f.read())

    ex = track_ui()
    ex.show()

    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(s, lambda signal, frame: sigint_handler(signal, ex))

    # catch the interpreter every now and then to be able to catch
    # signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec_())


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())
