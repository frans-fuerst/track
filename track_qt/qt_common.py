#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtCore #, Qt, uic, QtGui


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
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self._mylist = [('eins', 'zwei', 'drei')]
        self.header = ['1', '2', '3']
        self._sort_col = 0
        self._sort_reverse = False

    def rowCount(self, parent):
        return len(self._mylist)

    def columnCount(self, parent):
        return len(self._mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self._data(index.row(), index.column())

    def _data(self, row, column):
        return self._mylist[row][column]

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

    def _sort(self):
        self._mylist.sort(
            key=lambda tup: tup[self._sort_col],
            reverse=self._sort_reverse)


