#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Things needed by several components"""

from abc import ABC, abstractmethod

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


class TimechartDataprovider(ABC):
    @abstractmethod
    def date(self):
        pass

    @abstractmethod
    def initialized(self):
        pass

    @abstractmethod
    def begin_index(self):
        pass

    @abstractmethod
    def end_index(self):
        pass

    @abstractmethod
    def info_at(self, index: int):
        pass

    @abstractmethod
    def daily_note(self) -> str:
        pass

    @abstractmethod
    def category_at(self, index: int):
        pass

    @abstractmethod
    def current_minute(self):
        pass

    @abstractmethod
    def time_total(self):
        pass

    @abstractmethod
    def time_active(self):
        pass

    @abstractmethod
    def time_work(self):
        pass

    @abstractmethod
    def time_private(self):
        pass

    @abstractmethod
    def time_idle(self):
        pass

    @abstractmethod
    def clip_from(self, index: str) -> None:
        pass

    @abstractmethod
    def clip_to(self, index: int) -> None:
        pass


class change_emitter:
    def __init__(self, emitter):
        self._emitter = emitter

    def __enter__(self):
        self._emitter.layoutAboutToBeChanged.emit()
        return self

    def __exit__(self, _type, _value, _tb):
        self._emitter.layoutChanged.emit()


class SimpleQtThread(QtCore.QThread):
    def __init__(self, target):
        super().__init__()
        self.run = target
        self.start()
