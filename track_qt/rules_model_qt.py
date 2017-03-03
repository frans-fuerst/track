#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re

from track_qt.qt_common import matrix_table_model
from track_qt.qt_common import change_emitter
import track_base

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

class rules_model_qt(matrix_table_model):
    modified_rules = pyqtSignal()

    def __init__(self, parent, *args):
        matrix_table_model.__init__(self, parent, *args)
        self.header = ('M', 'regex', 'category', 'time')
        self._matching = []
        self._time = {}
        self._rules = []
        
    def supportedDragActions(self):
        return QtCore.Qt.MoveAction

    def update_categories_time(self, new_time):
        self._time = new_time

    def get_time_category(self, rule):
        category = rule[1]
        if category in self._time:
            return self._time[category]
        else:
            return 0

    def columnCount(self, parent):  # const
        return 4

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction|QtCore.Qt.CopyAction

    def rowCount(self, parent):
        return len(self._rules)

    def _data(self, row, column):  # const
        if column == 0:
            if len(self._matching) >= row+1 and self._matching[row]:
                return 'X'
        if column == 1:
            return self._rules[row][0]
        if column == 2:
            return self._rules[row][1]
        if column == 3: #time column
            return track_base.secs_to_dur(self.get_time_category(self._rules[row]))
        return None

    def __data__(self):  # const
        return ""

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

    #Makes it editable:
    def setData(self, index, value, role):
        if value != "":
            regex_str=str(value.toString())
            try:
                re.compile(regex_str)
                is_valid = True
            except re.error:
                is_valid = False
            if(is_valid):
                self._rules[index.row()][index.column()-1] = str(value.toString())
                self.modified_rules.emit()
                self.save_to_disk()
            else:
                self._rules[index.row()][index.column()-1] = "invalid regex"
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

    def add_rule(self):
        self._rules.insert(0, ["new rule", 0])

    def isEditable(self,index):
        return index.column() > 0

