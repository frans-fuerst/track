#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Things needed by several components"""

from PyQt5 import QtCore, QtGui

from ..core import Category


def CategoryColor(category):
    return {
        Category.IDLE: QtCore.Qt.white,
        Category.UNASSIGNED: QtGui.QColor(206, 92, 0),
        Category.WORK: QtCore.Qt.darkCyan,
        Category.PRIVATE: QtCore.Qt.cyan,
        Category.BREAK: QtCore.Qt.green,
    }.get(category, QtCore.Qt.red)


class change_emitter:
    def __init__(self, emitter):
        self._emitter = emitter

    def __enter__(self):
        self._emitter.layoutAboutToBeChanged.emit()
        return self

    def __exit__(self, type, value, tb):
        self._emitter.layoutChanged.emit()


class SimpleQtThread(QtCore.QThread):
    def __init__(self, target):
        super().__init__()
        self.run = target
        self.start()
