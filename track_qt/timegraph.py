#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import track_common

class timegraph(QtGui.QFrame):

    def __init__(self, parent):
        self._tracker = None
        super(timegraph, self).__init__(parent)
        self.setMouseTracking(True)
        self._selected = None

    def leaveEvent(self, e):
        self.select()

    def setTracker(self, tracker):
        self._tracker = tracker

    def paintEvent(self, e):

        super(timegraph, self).paintEvent(e)
        if self._tracker is None:
            return

        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def mouseMoveEvent(self, e):
        _index = self._tracker.begin_index() - 50 + e.x() - 1
        _cs, _activity = self._tracker.info(_index)

        _info_str =  "%s: %s (%s)" % (
                        track_common.mins_to_dur(_index), _activity,
                           track_common.mins_to_dur(_cs[1]-_cs[0]))
        # print("time: %d/%s" % (
        #     (e.x(), _info)))
        self.select(_cs[0], _cs[1])
        self.setToolTip(_info_str)

    def drawPoints(self, qp):
        if not self._tracker.initialized(): return
        
        x = self._tracker.begin_index()
        _start_index = self._tracker.begin_index() - 50
        for i in range(self.width() - 2):
            _index = _start_index + i

            # undo: evaluate always
            _is_private = self._tracker.is_private(_index)

            if i < 50 or _index > self._tracker.get_current_minute():
                # dark gray on borders of tracked time
                qp.setPen(QtCore.Qt.gray)
            elif self._tracker.get_current_minute() == _index:
                # black 'now' line
                qp.setPen(QtCore.Qt.black)
            elif not self._tracker.is_active(_index):
                qp.setPen(QtCore.Qt.white)
            elif _is_private:
                qp.setPen(QtCore.Qt.darkCyan)
            else:
                qp.setPen(QtCore.Qt.cyan)

            qp.drawLine(i + 1, 0, i + 1, self.height() - 2)

        if self._selected is None:
            return

        qp.setPen(QtCore.Qt.blue)
        for i in range(self._selected[0], self._selected[1] + 1):
            qp.drawLine(i - _start_index, 0 + 20, i - _start_index, self.height() - 2 - 20)

    def select(self, begin=None, end=None):
        if not begin:
            self._selected = None
        else:
            self._selected = (begin, end)
        self.update()

