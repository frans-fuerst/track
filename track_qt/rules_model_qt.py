#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines RulesModelQt
"""

import re

from typing import Any

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from track_qt.qt_common import change_emitter
import track_base
from track_base import log

class RulesModelQt(QtCore.QAbstractTableModel):
    modified_rules = pyqtSignal()

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self._header = ['Regex', 'Category']
        self._rules = []

    def columnCount(self, parent):
        return len(self._header)

    def rowCount(self, parent):
        return len(self._rules) + 1

    def headerData(self, column, orientation, role):
        return ((self._header[column] if column < len(self._header) else "???")
                if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal else
                None)

    def data(self, index, role):
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if column == 1:
                return QtCore.Qt.AlignHCenter
        if role not in {QtCore.Qt.DisplayRole, QtCore.Qt.EditRole}:
            return None
        if row >= len(self._rules):
            return None
        return self._rules[row][column]

    def sort(self, col, order):
        with change_emitter(self):
            self._sort_col = col
            self._sort_reverse = (order != QtCore.Qt.DescendingOrder)
            self._sort()

    def from_dict(self, rules):
        with change_emitter(self):
            self._rules = rules

    def to_dict(self):
        return self._rules

    def setData(self, index: QtCore.QModelIndex, value: str, role: int):
        if not role == QtCore.Qt.EditRole:
            return True
        if value is None:
            log().error("setData(value=None)")
            return False
        row, column = index.row(), index.column()
        current_rule = self._rules[row] if row < len(self._rules) else [".*", 2]

        if column == 0:
            try:
                re.compile(value)
            except re.error:
                print("invalid regex")
                return False
            current_rule[0] = value
        if column == 1:
            try:
                current_rule[1] = int(value)
            except ValueError:
                print("invalid int")
                return False

        if row < len(self._rules):
            self._rules[row] = current_rule
        else:
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self._rules.append(current_rule)
            self.endInsertRows()

        self.modified_rules.emit()
        return True

    def flags(self, index):
        defaultFlags = super().flags(index)
        if not index.isValid():
            return defaultFlags | QtCore.Qt.ItemIsDropEnabled

        return (
            defaultFlags
            | QtCore.Qt.ItemIsEditable
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsDragEnabled
            | QtCore.Qt.ItemIsDropEnabled)

    def supportedDragActions(self):
        return QtCore.Qt.MoveAction

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction #|QtCore.Qt.CopyAction

    def removeRow(self, row: int):
        if row >= len(self._rules):
            return
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._rules[row]
        self.endRemoveRows()
        self.modified_rules.emit()

    def removeRows(self, row, count):
        print("")

    def moveRow(self, index1, row1, index2, row2):
        print("")

    def moveRows(self, index1, a, b, index2, c):
        print("")

    def insertRow(self, index, arg0=None):
        print()

    def insertRows(self, row, count, parent=None):
        print(row, count, parent)
        result = super().insertRows(row, count, parent)
        print(result)
        self.modified_rules.emit()
        return result

    def update_categories_time(self, new_time):
        self._time = new_time

    def get_time_category(self, rule):
        return self._time.get(rule[1], 0)

    def check_string(self, string):
        print("check",string)
        for regex, category in self._rules:
            if re.search(regex, string):
                print("%r matches: %r" % (string, regex))
                return
        print("%r does not match" % string)
