#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned

"""Defines Mainwindow - a non application specific, platform independent MainWindow with
some common features
"""

import logging
from typing import Any, Dict, List, Set
import signal
import threading

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from .. import application_root_dir

from ..core.util import (
    log_system_info,
    log,
    open_in_directory_of,
)


class MainWindow(QtWidgets.QMainWindow):
    class QPlainTextEditLogger(logging.Handler):
        """Invokes main thread to write to log window"""
        def __init__(self, receiver) -> None:
            super().__init__()
            self.log_receiver = receiver
            self.initial_thread = threading.get_ident()

        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            if self.initial_thread == threading.get_ident():
                self.log_receiver.write_log(msg)
            else:
                QtCore.QMetaObject.invokeMethod(
                    self.log_receiver, 'write_log', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, msg))

    def __init__(self, _args=None) -> None:
        super().__init__()
        self.windowTitleChanged.connect(self.on_windowTitleChanged)
        with open_in_directory_of(__file__, "mainwindow.ui") as file:
            uic.loadUi(file, self, package="application.ui")

        for sig in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
            signal.signal(sig, lambda signal, frame: self.handle_signal(signal))

        # catch the interpreter every now and then to be able to catch signals
        self.idle_timer = QtCore.QTimer()
        self.idle_timer.timeout.connect(lambda: None)
        self.idle_timer.start(200)

        log_system_info()
        log().info("app dir: %r", application_root_dir())

        self.setMouseTracking(True)

    def setup_common_widgets(self):
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(0)
        font = QtGui.QFont("unexistent")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        self.log_view.setFont(font)
        logTextBox = self.QPlainTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter(
            "%(levelname)s %(asctime)s %(name)s: %(message)s", datefmt='%H:%M:%S'))
        logging.getLogger().addHandler(logTextBox)
        # self.pb_quit.clicked.connect(self.close)
        # self.pb_log.toggled.connect(self.toggle_log)
        # self.pb_log.setChecked(True)
        # self.pb_fullscreen.clicked.connect(self.toggle_fullscreen)

    def _initialize_tray_icon(self) -> QtWidgets.QSystemTrayIcon:
        def restore_window(reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
            if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
                self.tray_icon.hide()
                self.showNormal()

        tray_icon = QtWidgets.QSystemTrayIcon(self)
        tray_icon.setIcon(self.windowIcon())
        tray_icon.activated.connect(restore_window)
        return tray_icon

    def on_windowTitleChanged(self, title: str) -> None:
        QtCore.QCoreApplication.setApplicationName(title)
        self.setWindowIconText(title)

    @QtCore.pyqtSlot(str)
    def write_log(self, message):
        self.log_view.appendPlainText(message)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def toggle_log(self):
        self.log_view.setVisible(self.pb_log.isChecked())

    def toggle_fullscreen(self):
        (self.showNormal if self.isFullScreen() else
         self.showFullScreen)()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
            self.toggle_fullscreen()
        return super().keyPressEvent(event)

    def event(self, e):
        if not isinstance(e, (
                QtCore.QEvent,
                QtCore.QChildEvent,
                QtCore.QDynamicPropertyChangeEvent,
                QtGui.QPaintEvent,
                QtGui.QHoverEvent,
                QtGui.QMoveEvent,
                QtGui.QEnterEvent,
                QtGui.QResizeEvent,
                QtGui.QShowEvent,
                QtGui.QPlatformSurfaceEvent,
                QtGui.QWindowStateChangeEvent,
                QtGui.QKeyEvent,
                QtGui.QWheelEvent,
                QtGui.QMouseEvent,
                QtGui.QFocusEvent,
                QtGui.QHelpEvent,
                QtGui.QHideEvent,
                QtGui.QCloseEvent,
                QtGui.QInputMethodQueryEvent,
                QtGui.QContextMenuEvent,
                )):
            log().warning("unknown event: %r %r", e.type(), e)
        return super().event(e)

    def closeEvent(self, event):
        for handler in logging.getLogger().handlers:
            if isinstance(handler, self.QPlainTextEditLogger):
                logging.getLogger().removeHandler(handler)
                break
        return super().closeEvent(event)

    def handle_signal(self, sig: int) -> None:
        """Handle posix signals, i.e. shut down on CTRL-C"""
        log().info(
            "got signal %s(%d)",
            dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                 if v.startswith('SIG') and not v.startswith('SIG_')).get(sig, "unknown"),
            sig)
        if sig == signal.SIGINT:
            self.close()
