#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic

def mins_to_str(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"h "
        _minutes %= 60
    _result += str(_minutes ) + "m"
    return _result

class timegraph(QtGui.QFrame):

    def __init__(self, parent):
        self._tracker = None
        super(timegraph, self).__init__(parent)
        self.setMouseTracking(True)

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
        _info = mins_to_str(_index) + ": " + str(self._tracker.info(_index))
        print("time: %d/%s" % (
            (e.x(), _info)))
        self.setToolTip(_info)

    def drawPoints(self, qp):
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

if __name__ == '__main__':
    print('this is just the bargraph widget. run track.py')

