#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys

import track_qt

from PyQt5 import QtWidgets, QtCore, Qt, uic

class test_ui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        tg = track_qt.timegraph(self)
        self.show()
        q = QtCore.QTimer()
        q.singleShot(1000, self.quit)
    
    def quit(self):
        print("quit()")
        QtCore.QCoreApplication.instance().quit()

def test_timegraph():
    app = QtWidgets.QApplication(sys.argv)
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

