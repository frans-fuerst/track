#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic

class timegraph(QtGui.QFrame):

    def __init__(self, parent):
        self._tracker = None
        super(timegraph, self).__init__(parent)
    
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

    def drawPoints(self, qp):
      
        _start_index = self._tracker.first_index() - 50
        for i in range(self.width() - 2):
            _index = _start_index + i
            if i < 50 or _index > self._tracker.get_current_minute():
                # dark gray on borders of tracked time
                qp.setPen(QtCore.Qt.gray)
            elif self._tracker.get_current_minute() == _index:
                # black 'now' line
                qp.setPen(QtCore.Qt.black)
            elif not self._tracker.is_active(_index):
                qp.setPen(QtCore.Qt.white)
            elif self._tracker.is_private(_index):
                qp.setPen(QtCore.Qt.darkCyan)
            else:
                qp.setPen(QtCore.Qt.cyan)

            qp.drawLine(i + 1, 0, i + 1, self.height() - 2)

if __name__ == '__main__':
    print('this is just the bargraph widget. run track.py')
    
