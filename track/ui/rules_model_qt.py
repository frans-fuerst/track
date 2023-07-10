#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines RulesModelQt
"""

import re
from typing import Any

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from ..core.util import log
from .qt_common import change_emitter


class RulesModelQt(QtCore.QAbstractTableModel):
    rulesChanged = pyqtSignal()

    def __init__(self, *, rules=None, parent=None):
        super().__init__(parent)
        self._rules = rules or []

    def headerData(self, column: int, orientation, role: QtCore.Qt.ItemDataRole) -> Any:
        return (
            ("Regex", "Category")[column]
            if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal
            else None
        )

    def columnCount(self, _parent: QtCore.QModelIndex = None) -> int:
        return 2

    def rowCount(self, _parent: QtCore.QModelIndex = None) -> int:
        return len(self._rules) + 1

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole) -> Any:
        return (
            (
                (
                    self._rules[index.row()][index.column()]
                    if index.row() < len(self._rules)
                    else ("", 1)[index.column()]
                    if role == QtCore.Qt.DisplayRole
                    else (".*", 2)[index.column()]
                )
                if role in {QtCore.Qt.DisplayRole, QtCore.Qt.EditRole}
                else None
            )
            if index.isValid()
            else None
        )

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

        self.rulesChanged.emit()
        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        if index.row() < len(self._rules):
            return (
                QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsDragEnabled
            )
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def supportedDropActions(self) -> bool:
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction

    def removeRow(self, row: int):
        if row >= len(self._rules):
            return
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._rules[row]
        self.endRemoveRows()
        self.rulesChanged.emit()

    def insertRows(self, row, count, parent=None):
        print(row, count, parent)
        result = super().insertRows(row, count, parent)
        print(result)
        self.rulesChanged.emit()
        return result

    def moveRow(
        self,
        sourceParent: QtCore.QModelIndex,
        sourceRow: int,
        destinationParent: QtCore.QModelIndex,
        destinationChild: int,
    ) -> bool:
        row_a, row_b = max(sourceRow, destinationChild), min(sourceRow, destinationChild)
        self.beginMoveRows(QtCore.QModelIndex(), row_a, row_a, QtCore.QModelIndex(), row_b)
        self._rules.insert(destinationChild, self._rules.pop(sourceRow))
        self.endMoveRows()
        self.rulesChanged.emit()
        return True

    def set_rules(self, rules):
        with change_emitter(self):
            self._rules = rules
            self.rulesChanged.emit()

    def rules(self):
        return self._rules

    def check_string(self, string: str) -> None:
        print("check", string)
        for regex, category in self._rules:
            if re.search(regex, string):
                print("%r matches: %r" % (string, regex))
                return
        print("%r does not match" % string)
