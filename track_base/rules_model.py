#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import json

class rules_model():
    def __init__(self):
        self._matching = []
        self._rules = []

    def columnCount(self, parent):  # const
        return 3

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
        return None

    def __data__(self):  # const
        return self._rules

    def from_dict(self, data):
        pass

    def highlight_string(self, string):
        # todo: mutex
        self._matching = []
        for r, c in self._rules:
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

    def setData(self, index, value, role):
        if value != "":
            regex_str = str(value.toString())
            try:
                re.compile(regex_str)
                is_valid = True
            except re.error:
                is_valid = False
            
            if is_valid:
                self._rules[index.row()][index.column()-1] = str(value.toString())
            else:
                self._rules[index.row()][index.column()-1] = "invalid regex"
        return True

    def add_rule(self):
        self._rules.insert(0, ["new rule", 0])
