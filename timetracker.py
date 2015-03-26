#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtCore #, Qt, uic, QtGui

from datetime import datetime

import idle
import applicationinfo
import json


def secs_to_str(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"m "
        _minutes %= 60
    _result += str(_minutes ) + "s"
    return _result

def seconds_since_midnight():
    now = datetime.now()
    return int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())


def minutes_since_midnight():
    #return int(seconds_since_midnight() / 2)
    return int(seconds_since_midnight() / 60)


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
        self.layoutAboutToBeChanged.emit()
        self._sort_col = col
        self._sort_reverse = (order != QtCore.Qt.DescendingOrder)
        self._sort()
        self.layoutChanged.emit()
        
    def _sort(self):
        self._mylist.sort(
            key=lambda tup: tup[self._sort_col],
            reverse=self._sort_reverse)

global_app_categories = {}  # acc -> category

class application():
    """ holds immutable information about an application
    """
    def __init__(self, identifier):
        self._identifier = identifier

    def __str__(self):
        return self._identifier
            

class app_count_category():
    """ combines an app identifier, a category and a time count to something
        that behaves like a list
    """
    
    def __init__(self, title, count=0):
        self._app = application(title)
        self._count = count

    def __str__(self):
        return "%s (%d)" % (self._app, self._count)

    def __getitem__(self, index):
        if index == 0:
            return self._app._identifier
        elif index == 1:
            return self._count
        elif index == 2:
            return global_app_categories[self._app]
        else:
            raise Exception("must not happen")

        
class active_applications(matrix_table_model):
    def __init__(self, parent, *args):
        matrix_table_model.__init__(self, parent, *args)
        self.header = ['application title', 'time', 'category']
        self._mylist = [] # list of app_count_category instances
        self._apps = {}   # app identifier -> app_count_category instance

    def get_indexed_data(self):
        return {self._apps.keys()[i]:(i, self._apps.values()[i]) 
                    for i in range(len(self._apps))}

    def set_indexed_data(self, data):
        self.layoutAboutToBeChanged.emit()

        #_appdata = [app_count_category([a[0], a[1]]) 
        #                for a in _struct['apps']]

        for acc in data:
            print(acc.__dict__)
        global global_app_categories
        print(global_app_categories)
        print("============")
        global_app_categories = {acc._app: 0 for acc in data}
        print(global_app_categories)

        self._mylist = data
        self._apps = {acc._app._identifier: acc for acc in self._mylist}
        
        self._sort()
        self.layoutChanged.emit()

    def columnCount(self, parent):
        return 3

    def _data(self, row, column):
        if column == 1:
            return secs_to_str(self._mylist[row][column])
        return self._mylist[row][column]
    
    def get_and_update(self, title):
        self.layoutAboutToBeChanged.emit()
        
        if title not in self._apps:
            _new = app_count_category(title)
            
            self._apps[title] = _new
            self._mylist.append(_new)
            
            if "Firefox" in title:
                global_app_categories[_new._app] = 1
            else:
                global_app_categories[_new._app] = 0
                
        _result = self._apps[title]
            
        _result._count += 1

        self._sort()

        """
        print('===')
        for i in self._mylist:
            print(i)
        """
        
        # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.layoutChanged.emit()
        
        return _result._app

       
class minute():
    """ a minute holds a category and a list of apps
    """
    def __init__(self, category=0, apps={}):
        self._category = 0
        self._apps = apps # app -> count
        
    def _rebuild(self):
        _categories = {} # category -> sum
        for a, c in self._apps.items():
            try:
                _cat = global_app_categories[a]
                if _cat not in _categories:
                    _categories[_cat] = c
                else:
                    _categories[_cat] += c
            except:
                pass
                    
        self._category = _categories.keys()[
                                _categories.values().index(
                                    max(_categories.values()))]
        
    def add(self, app_instance):
        if app_instance not in self._apps:
            self._apps[app_instance] = 1
        else:
            self._apps[app_instance] += 1
        self._rebuild()
    

class time_tracker():

    def __init__(self, parent):
        self._idle_current = 0
        self._max_minute = 0
        self._current_app_title = ""
        self._current_process_exe = ""
        self._user_is_active = True

        # -- persist
        self._start_minute = minutes_since_midnight()
        self._applications = active_applications(parent)
        self._minutes = {}  # min -> [apps], category

    def __cmp__(self, other):
        pass

    def load(self):
        _file_name = "load.json"
        with open(_file_name) as _file:
            _struct = json.load(_file)
        assert 'apps' in _struct
        assert 'minutes' in _struct

        _appdata = [app_count_category(a[0], a[1]) 
                        for a in _struct['apps']]

        _new_minutes = {m: minute(c, {_appdata[_a]: 1 for _a in a}) 
                                        for m, c, a in _struct['minutes']}

        print("apps: %s" % len(_appdata))
        print("mins: %s" % len(_new_minutes))

        # with lock
        _app_data = self._applications.set_indexed_data(_appdata)
        self._minutes = _new_minutes
        print("<<<<<")


    def save(self):
        _file_name = "track.json"
        _app_data = self._applications.get_indexed_data()
        # print(_app_data)
        _struct = {
                'start':0,
                'end':0,
                'apps':
                    [(k, c._count) 
                        for k, (i, c) in _app_data.items()],
                'minutes': 
                    [(m, c._category, [_app_data[a._identifier][0] 
                        for a in c._apps.keys()])
                            for m, c in self._minutes.items()]
            }
        with open(_file_name, 'w') as _file:
            json.dump(_struct, _file, 
                      sort_keys=True,
                      indent=4, separators=(',', ': '))

    def get_applications_model(self):
        return self._applications
        
    def update(self):
        try:
            _minute_index = minutes_since_midnight()

            self._max_minute = _minute_index

            
            self._user_is_active = True
       
            self._idle_current = idle.getIdleSec()
            self._current_app_title = applicationinfo.get_active_window_title() 
            self._current_process_exe = applicationinfo.get_active_process_name()
            if self._idle_current > 10:
                self._user_is_active = False
                return

            _app = self._applications.get_and_update(self._current_app_title)
            
            if _minute_index not in self._minutes:
                self._minutes[_minute_index] = minute()
            self._minutes[_minute_index].add(_app)
        except applicationinfo.UncriticalException as e:
            pass

    def first_index(self):
        return self._start_minute

    def start_time(self):
        _s = self._start_minute
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def now(self):
        _s = minutes_since_midnight()
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def is_active(self, minute):
        if minute in self._minutes:
            return True
        return False

    def is_private(self, minute):
        if minute not in self._minutes:
            return False
        return self._minutes[minute]._category != 0

    def get_time_total(self):
        return minutes_since_midnight() - self._start_minute + 1

    def get_time_active(self):
        return len(self._minutes)

    def get_time_work(self):
        r = 0
        for i, m in self._minutes.items():
            r += m._category == 0
        return r

    def get_time_private(self):
        r = 0
        for i, m in self._minutes.items():
            r += m._category != 0
        return r

    def get_time_idle(self):
        return self.get_time_total() - len(self._minutes)

    def get_current_minute(self):
        return self._max_minute

    def get_idle(self):
        return self._idle_current
        
    def get_current_app_title(self):
        return self._current_app_title
        
    def get_current_process_name(self):
        return self._current_process_exe
        
    def user_is_active(self):
        return self._user_is_active


if __name__ == '__main__':
    print('this is the timetracker core module. run track.py')

