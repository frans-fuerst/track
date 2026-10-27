#!/usr/bin/env python3
"""System test: constructs the timegraph widgets inside a real QApplication"""

import sys

import pytest
from PyQt5 import QtCore, QtWidgets

from track.ui.timegraph import EvaluationWidget

pytestmark = pytest.mark.system


def test_timegraph_shows_and_quits():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setCentralWidget(EvaluationWidget())
    window.show()
    QtCore.QTimer.singleShot(500, app.quit)
    app.exec_()
