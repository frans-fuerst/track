#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt, uic
import sys
import random
import signal
import logging

# http://thp.io/2007/09/x11-idle-time-and-focused-window-in.html

import ctypes
import os

class XScreenSaverInfo( ctypes.Structure):
  """ typedef struct { ... } XScreenSaverInfo; """
  _fields_ = [('window',      ctypes.c_ulong), # screen saver window
              ('state',       ctypes.c_int),   # off,on,disabled
              ('kind',        ctypes.c_int),   # blanked,internal,external
              ('since',       ctypes.c_ulong), # milliseconds
              ('idle',        ctypes.c_ulong), # milliseconds
              ('event_mask',  ctypes.c_ulong)] # events

xlib = ctypes.cdll.LoadLibrary( 'libX11.so')
dpy = xlib.XOpenDisplay( os.environ['DISPLAY'])
root = xlib.XDefaultRootWindow( dpy)
xss = ctypes.cdll.LoadLibrary( 'libXss.so')
xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
xss_info = xss.XScreenSaverAllocInfo()
xss.XScreenSaverQueryInfo( dpy, root, xss_info)
print "Idle time in milliseconds: %d" % ( xss_info.contents.idle, )
       
class track_ui(QtGui.QWidget):

    def __init__(self):
        super(track_ui, self).__init__()
        print('init')
        self.show()

        self.initUI()
        
    def initUI(self):      

        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Points')
        self.show()

    def paintEvent(self, e):

        print('paint')
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def drawPoints(self, qp):
      
        qp.setPen(QtCore.Qt.red)
        size = self.size()
        
        for i in range(1000):
            x = random.randint(1, size.width()-1)
            y = random.randint(1, size.height()-1)
            qp.drawLine(i, 100, i, 200)   

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
