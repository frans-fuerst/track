#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt5 import QtCore

class change_emitter:
    def __init__(self, emitter):
        self._emitter = emitter

    def __enter__(self):
        self._emitter.layoutAboutToBeChanged.emit()
        return self

    def __exit__(self, type, value, tb):
        self._emitter.layoutChanged.emit()


class matrix_table_model(QtCore.QAbstractTableModel):
    """ generic model holding a sortable list of list-likes
    """
    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self.header = ['1', '2', '3']
        self._sort_col = 0
        self._sort_reverse = False

    def rowCount(self, parent):
        return len(self._mylist)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, col, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
                   role == QtCore.Qt.DisplayRole):
            return self.header[col]
        return None

    def sort(self, col, order):
        with change_emitter(self):
            self._sort_col = col
            self._sort_reverse = (order != QtCore.Qt.DescendingOrder)
            self._sort()
