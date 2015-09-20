#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#from PyQt4 import QtCore #, Qt, uic, QtGui

import re

#from desktop_usage_info import idle
#from desktop_usage_info import applicationinfo
#import track_common
import track_qt
import qt_common
import json
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal


class rules_model(qt_common.matrix_table_model):
    _filename="regex_rules";
    modified_rules= pyqtSignal()
    def __init__(self, parent, *args):
        track_qt.matrix_table_model.__init__(self, parent, *args)
        self.header = ['M', 'regex', 'category']
        self.load_from_disk();
        self._matching = []

    def columnCount(self, parent):  # const
        return 3

    def rowCount(self, parent):
        return len(self._rules) + 1

    #used by QT to display the data
    def _data(self, row, column):  # const
        if row == 0:
            return(None, ' - add new - ', None)[column]
        if column == 0:
            if len(self._matching) >= row and self._matching[row - 1]:
                return 'X' 
        if column == 1:
            return self._rules[row - 1][0]
        if column == 2:
            return self._rules[row - 1][1]
        return None
    
    def __data__(self):  # const
        return ""

    def from_dict(self, data):
        pass

    #This functions marks the Regex that is being recorded at the moment.
    def highlight_string(self, string):
        with track_qt.change_emitter(self):
            self._matching = []
            for i, [r, c] in enumerate(self._rules):
                if re.search(r, string):
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
    def setData(self, index, value,  role):
        if value!="":
            regex_str=str(value.toString())
            try:
                re.compile(regex_str)
                is_valid = True
            except re.error:
                is_valid = False
            if(is_valid):
                self._rules[index.row()-1][index.column()-1] = str(value.toString())
                self.modified_rules.emit()
                self.save_to_disk()
            else:
                self._rules[index.row()-1][index.column()-1] = "invalid regex"
        return True
    def flags(self, index):
        if (self.isEditable(index)):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def add_rule(self):
        self._rules.insert(0, ["new rule", 0])
    def isEditable(self,index):
        if (index.column()>0):
            return True
        else:
            return False
    def load_from_disk(self):
        _file_name = self._filename
        try:
            with open(_file_name) as _file:
                _struct = json.load(_file)
        except:
            _struct=[[".* - Mozilla Firefox.*", 1],
                       [".*gedit.*", 0]]
        self._rules = _struct;
    def save_to_disk(self):
        _file_name = self._filename
        with open(_file_name, 'w') as _file:
            json.dump(self._rules, _file,
                      sort_keys=False) #, indent=4, separators=(',', ': '))
            
