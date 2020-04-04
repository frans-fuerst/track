#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtGui, QtCore

from ..core import common
from . import CategoryColor


class Timegraph(QtWidgets.QFrame):
    clipFromClicked = QtCore.pyqtSignal(int)
    clipToClicked = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self._tracker = None
        self.setMouseTracking(True)
        self._selected = None

    def leaveEvent(self, _event):
        self.select()

    def setTracker(self, tracker):
        self._tracker = tracker

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._tracker is None:
            return

        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def mouseMoveEvent(self, event):
        _index = self._tracker.begin_index() - 50 + event.x() - 1
        _cs, _activity = self._tracker.info(_index)

        _info_str = "%s: %s (%s)" % (
            common.mins_to_dur(_index),
            _activity,
            common.mins_to_dur(_cs[1]-_cs[0]))
        self.select(_cs[0], _cs[1])
        self.setToolTip(_info_str)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        index = self._tracker.begin_index() - 50 + event.x() - 1
        clip_from = menu.addAction("clip before %s (erases data!)" % common.mins_to_dur(index))
        clip_to = menu.addAction("clip after %s (erases data!)" % common.mins_to_dur(index))
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == clip_from:
            self.clipFromClicked.emit(index)
        if action == clip_to:
            self.clipToClicked.emit(index)

    def drawPoints(self, qp):
        if not self._tracker.initialized():
            return

        _start_index = self._tracker.begin_index() - 50
        for i in range(self.width() - 2):
            _index = _start_index + i
            qp.setPen(
                # dark gray on borders of tracked time
                QtCore.Qt.gray if i < 50 or _index > self._tracker.get_current_minute() else
                # black 'now' line
                QtCore.Qt.black if self._tracker.get_current_minute() == _index else
                CategoryColor(self._tracker.category_at(_index)))

            qp.drawLine(i + 1, 0, i + 1, self.height() - 2)

        if self._selected is None:
            return

        qp.setPen(QtCore.Qt.blue)
        for i in range(self._selected[0], self._selected[1] + 1):
            qp.drawLine(i - _start_index, 0 + 20, i - _start_index, self.height() - 2 - 20)

    def select(self, begin=None, end=None):
        self._selected = (begin, end) if begin is not None and end is not None else None
        self.update()
