#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtCore #, Qt, uic, QtGui

from datetime import datetime

import idle
import applicationinfo

def seconds_since_midnight():
    now = datetime.now()
    return int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())


def minutes_since_midnight():
    #return int(seconds_since_midnight() / 2)
    return int(seconds_since_midnight() / 60)

class matrix_table_model(QtCore.QAbstractTableModel):
    def __init__(self, parent, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self._mylist = [('eins', 'zwei', 'drei')]
        self.header = ['1', '2', '3']

    def rowCount(self, parent):
        return len(self._mylist)
        
    def columnCount(self, parent):
        return len(self._mylist[0])
        
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self._mylist[index.row()][index.column()]
        
    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None
        
    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        #self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self._mylist = sorted(self._mylist,
            key=operator.itemgetter(col))
        if order == QtCore.Qt.DescendingOrder:
            self._mylist.reverse()
        #self.emit(SIGNAL("layoutChanged()"))
        self.layoutChanged.emit()
        
        
class active_applications(matrix_table_model):
    def __init__(self, parent, *args):
        matrix_table_model.__init__(self, parent, *args)
        self._mylist = []
        self.header = ['application title', 'time', 'category']
        self._apps = {}

    def columnCount(self, parent):
        return 3
    
    def add(self, app):
        self.layoutAboutToBeChanged.emit()
        if app not in self._apps:
            _new = [app, 1, None]
            
            self._apps[app] = _new
            self._mylist.append(_new)
        else:
            self._apps[app][1] += 1
        # print('===')
        # for i in self._mylist:
        #     print(i)
        # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.layoutChanged.emit()
            
class time_tracker():

    def __init__(self, parent):
        self._start_minute = minutes_since_midnight()
        self._minutes = {}
        self._max_minute = 0
        self._idle = 0
        self._current_app_title = ""
        self._current_process_exe = ""
        self._user_is_active = True
        self._applications = active_applications(parent)
        
    def get_applications_model(self):
        return self._applications
        
    def update(self):
   
        self._idle = idle.getIdleSec()
        self._current_app_title = applicationinfo.get_active_window_title() 
        self._current_process_exe = applicationinfo.get_active_process_name()
        
        _minute_index = minutes_since_midnight()

        self._max_minute = _minute_index

        if self._idle > 5:
            self._user_is_active = False
            return
        self._user_is_active = True
 
        self._applications.add(self._current_app_title)
        
        if _minute_index not in self._minutes:
            self._minutes[_minute_index] = []
        self._minutes[_minute_index].append(self._current_app_title)

    def first_index(self):
        return self._start_minute

    def start_time(self):
        _s = self._start_minute
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def is_active(self, minute):
        if minute in self._minutes:
            return True
        return False

    def is_private(self, minute):
        return int(minute / 2) % 2 == 0

    def get_active_time(self):
        _result = ""
        _minutes = len(self._minutes)
        if _minutes >= 60:
            _result = str(int(_minutes / 60))+"h "
            _minutes %= 60
        _result += str(_minutes ) + "m"
        return _result

    def get_current_minute(self):
        return self._max_minute

    def get_idle(self):
        return self._idle
        
    def get_current_app_title(self):
        return self._current_app_title
        
    def get_current_process_name(self):
        return self._current_process_exe
        
    def user_is_active(self):
        return self._user_is_active


if __name__ == '__main__':
    print('this is the timetracker core module. run track.py')

