#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import timegraph
import signal
import sys

from PyQt4 import QtGui, QtCore, Qt, uic

class test_ui(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        tg = timegraph.timegraph(self)
        self.show()
        #QtGui.QApplication.quit()


def sigint_handler(*args):
    QtGui.QApplication.quit()

def test_timegraph():
    signal.signal(signal.SIGINT, sigint_handler)
    app = QtGui.QApplication(sys.argv)

    x = test_ui()
    
    # catch the interpreter every now and then to be able to catch
    # signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec_())

if __name__ == '__main__':
    test_timegraph()

