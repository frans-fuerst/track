#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re

from typing import Any

from track_qt.qt_common import matrix_table_model
from track_qt.qt_common import change_emitter
import track_base

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

class RulesModelQt(matrix_table_model):
    modified_rules = pyqtSignal()

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self.header = ['M', 'Regex', 'Category', 'Spent']
        self._matching = []
        self._time = {}
        self._rules = []

    def supportedDragActions(self):
        return QtCore.Qt.MoveAction

    def update_categories_time(self, new_time):
        self._time = new_time

    def get_time_category(self, rule):
        return self._time.get(rule[1], 0)

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction|QtCore.Qt.CopyAction

    def rowCount(self, parent):
        return len(self._rules) + 1

    def data(self, index, role):
        if not (index.isValid() and role in {QtCore.Qt.DisplayRole, QtCore.Qt.EditRole}):
            return None
        row, column = index.row(), index.column()
        if row >= len(self._rules):
            return None
        return ("?" if column == 0 else
                self._rules[row][column - 1] if column < 3 else
                track_base.secs_to_dur(self.get_time_category(self._rules[row])))

    def from_dict(self, data):
        with change_emitter(self):
            self._rules = data['rules']

    def highlight_string(self, string):
        with change_emitter(self):
            self._matching = []
            for i, (r, c) in enumerate(self._rules):
                if re.search(r, string):
                    # print("'%s' matches" % r)
                    self._matching.append(True)
                else:
                    self._matching.append(False)

    def get_first_matching_key(self, app):
        _string = app.generate_identifier()
        for r, c in self._rules:
            if re.search(r, _string):
                return c
        return 0

    def setData(self, index: QtCore.QModelIndex, value: str, role: int):
        assert role == QtCore.Qt.EditRole
        row, column = index.row(), index.column()
        current_rule = self._rules[row] if row < len(self._rules) else [".*", 0]

        if column == 1:
            try:
                re.compile(value)
            except re.error:
                print("invalid regex")
                return False
            current_rule[0] = value
        if column == 2:
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
        # TODO: save rule changes to disk
        return True

    def flags(self, index):
        if (self.isEditable(index)):
            return (QtCore.Qt.ItemIsEditable |
                    QtCore.Qt.ItemIsEnabled |
                    QtCore.Qt.ItemIsSelectable |
                    QtCore.Qt.ItemIsDragEnabled |
                    QtCore.Qt.ItemIsDropEnabled)
        else:
            return (QtCore.Qt.ItemIsEnabled |
                    QtCore.Qt.ItemIsSelectable|
                    QtCore.Qt.ItemIsDropEnabled)

    def isEditable(self,index):
        return index.column() > 0

