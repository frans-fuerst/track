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
        q = QtCore.QTimer()
        q.singleShot(1000, self.quit)
    
    def quit(self):
        print("quit()")
        QtCore.QCoreApplication.instance().quit()

def test_timegraph():
    app = QtGui.QApplication(sys.argv)
    mainwindow = test_ui()
    signal.signal(signal.SIGINT, lambda signal, 
                  frame: sigint_handler(signal, mainwindow))
    
    # catch the interpreter every now and then to be able to catch
    # signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    app.exec_()

if __name__ == '__main__':
    test_timegraph()

