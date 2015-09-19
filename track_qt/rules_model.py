#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#from PyQt4 import QtCore #, Qt, uic, QtGui

import re

#from desktop_usage_info import idle
#from desktop_usage_info import applicationinfo
#import track_common
import track_qt
import qt_common
from PyQt4 import QtCore 


class rules_model(qt_common.matrix_table_model):

    def __init__(self, parent, *args):
        track_qt.matrix_table_model.__init__(self, parent, *args)
        self.header = ['M', 'regex', 'category']
        self._rules = [[".* - Mozilla Firefox.*", 1],
                       [".*gedit.*", 0]]
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
            self._rules[index.row()-1][index.column()-1] = str(value.toString())
        return True
    def flags(self, index):
        if (self.isEditable(index)):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable 
    def isEditable(self,index):
        if (index.column()>0):
            return True
        else:
            return False
