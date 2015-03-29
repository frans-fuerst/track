#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtCore #, Qt, uic, QtGui

from datetime import datetime

import idle
import applicationinfo
import json
import operator
import time


def secs_to_str(mins):
    _result = ""
    _minutes = mins
    if _minutes >= 60:
        _result = str(int(_minutes / 60))+"m "
        _minutes %= 60
    _result += str(_minutes ) + "s"
    return _result


def today_str():
    return datetime.fromtimestamp(time.time()).strftime('%Y%m%d')

def today_int():
    now = datetime.now()
    return now.year*10000 + now.month * 100 + now.day


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


class app_info():
    
    def __init__(self, windowtitle="", cmdline=""):
        self._wndtitle = windowtitle
        self._cmdline = cmdline
        self._category = 0
        self._count = 0
        
    def __eq__(self, other):
        if not self._wndtitle == other._wndtitle:
            return False
        if not self._cmdline == other._cmdline:
            return False
        if not self._category == other._category:
            return False
        if not self._count == other._count:
            return False
        return True
    
    def __hash__(self):
        x = hash((self._wndtitle, self._cmdline))
        return x
    
    def __str__(self):
        return "%s - [%d %d]" % (self._wndtitle, self._category, self._count)
    
    def load(self, data):
        self._wndtitle, self._category, self._count, self._cmdline = data
        return self
    
    def __data__(self):  # const
        return (self._wndtitle, self._category, self._count, self._cmdline)

    def generate_identifier(self):
        return self._wndtitle


class minute():
    """ a minute holds a category and a list of apps
    """
    def __init__(self, category=0, apps=None):
        self._category = 0
        if apps is None:
            self._apps = {}
        else:
            self._apps = apps  # app_info -> count

    def __eq__(self, other):
        if not self._category == other._category:
            return False
        if not self._apps == other._apps:
            for a, c in self._apps.items():
                print("s: %s:'%s' - %d" % (hex(id(a)), a, c))
            for a, c in other._apps.items():
                print("o: %s - %d" % (a, c))
            return False
        return True
    
    def dump(self):
        print("category %d" % self._category)
            
    def init(self, data):
        self._category, self._apps = data
        return self
    
    def _rebuild(self):
        if len(self._apps) == 0:
            return 0  # todo: need undefined
        
        _categories = {} # category -> sum
        for a, c in self._apps.items():
            try:
                if a._category not in _categories:
                    _categories[a._category] = c
                else:
                    _categories[a._category] += c
            except:
                pass

        self._category = _categories.keys()[
                                _categories.values().index(
                                    max(_categories.values()))]
        # print(self._category)

    def add(self, app_instance):
        if app_instance not in self._apps:
            self._apps[app_instance] = 1
        else:
            self._apps[app_instance] += 1
        self._rebuild()
        

# todo: separate qt model
class active_applications(matrix_table_model):
    ''' the data model which holds all application usage data for one
        day. That is:

        app_data:  {app_id: application}

        minutes:   {i_min => [app_id], i_cat}

        where

        application:  (i_secs, i_cat, s_title, s_process)        


        model_list:
            * sortable by key
            * can be done with list of keys sorted by given value
            [(app_id, i_secs, i_cat)]

    '''

    def __init__(self, parent, *args):
        matrix_table_model.__init__(self, parent, *args)
        self.header = ['application title', 'time', 'category']
        self._index_min = None
        self._index_max = None
        self._sorted_keys = []
        
        # to be persisted
        self._apps = {}     # app identifier => app_info instance
        self._minutes = {}  # i_min          => minute

    def clear(self):
        self.layoutAboutToBeChanged.emit()  # todo: this is not threadsafe
        self._index_min = None
        self._index_max = None
        self._apps = {}     # app identifier => app_info instance
        self._minutes = {}  # i_min          => minute
        self.layoutChanged.emit()

    def rowCount(self, parent):
        return len(self._sorted_keys)

    def columnCount(self, parent):  # const
        return 3

    def _data(self, row, column):  # const
        if column == 0:
            return self._apps[self._sorted_keys[row]]._wndtitle
        elif column == 1:
            return secs_to_str(self._apps[self._sorted_keys[row]]._count)
        elif column == 2:
            return self._apps[self._sorted_keys[row]]._category
        return 0
    
    def __eq__(self, other):
        if not self._apps == other._apps:
            return False
        if not self._minutes == other._minutes:
            for m in self._minutes:
                pass
            return False
        return True

    def _sort(self):
        # print([x[1]._count for x in self._apps.items()])
        # print(self._sort_col)
        if self._sort_col == 0:
            self._sorted_keys = [x[0] for x in sorted(
                self._apps.items(), 
                key=lambda x: x[1]._wndtitle, 
                reverse=self._sort_reverse)]
        elif self._sort_col == 1:
            self._sorted_keys = [x[0] for x in sorted(
                self._apps.items(), 
                key=lambda x: x[1]._count,
                reverse=self._sort_reverse)]
        elif self._sort_col == 2:
            self._sorted_keys = [x[0] for x in sorted(
                self._apps.items(), 
                key=lambda x: x[1]._category, 
                reverse=self._sort_reverse)]
    
    def __data__(self):  # const
        """ we have to create an indexed list here because the minutes
            dict has to store references to app_info.
            intermediate: _indexed: {app_id => (i_index, app_info)} 
            result:    app:     [app_info]
                       minutes: {i_minute: (i_category, [(app_info, i_count)])}
            
            """
        _indexed = {a: i for i, a in enumerate(self._apps.values())}
        _apps = [d[1] for d in sorted([(e[1], e[0].__data__()) 
                                       for e in _indexed.items()])]
        # print(_apps)
        _minutes = {i: (m._category, [(_indexed[a], c) 
                                      for a, c in m._apps.items()])
                    for i, m in self._minutes.items()}
        
        #print(_minutes)
                
        return { 'apps': _apps,
                 'minutes': _minutes}

    def from_dict(self, data):
        assert 'apps' in data
        assert 'minutes' in data
        _a = data['apps']
        _indexed = [app_info().load(d) for d in _a]
        _m = data['minutes']
        _minutes = {
            int(i) : minute().init(
                (
                    m[0],
                    {
                        _indexed[a]: c for a, c in m[1]
                    }
                )
            ) 
            for i, m in _m.items()
        }
        
        # x = {i:len({a:0 for a in i}) for i in l}
        _apps = {a.generate_identifier(): a for a in _indexed}
        self.layoutAboutToBeChanged.emit()

        self._apps = _apps
        self._minutes = _minutes

        if len(self._minutes) > 0:
            self._index_min = min(self._minutes.keys())
            self._index_max = max(self._minutes.keys())
        else:
            self._index_min = None
            self._index_max = None
            
        self._sort()
        self.layoutChanged.emit()
        
        # print(_minutes)
    
    def begin_index(self):  # const
        return self._index_min if self._index_min else 0

    def end_index(self):  # const
        return self._index_max if self._index_max else 0

    def update(self, minute_index, app):
        self.layoutAboutToBeChanged.emit()  # todo: this is not threadsafe
        
        _app_id = app.generate_identifier()

        if _app_id not in self._apps:
            self._apps[_app_id] = app

            if "Firefox" in _app_id:
                app._category = 1
            else:
                app._category = 0
        # print([a._category for a in self._apps.values()])
        _app = self._apps[_app_id]
        _app._count += 1

        if minute_index not in self._minutes:
            self._minutes[minute_index] = minute()
            if not self._index_min or self._index_min > minute_index:
                self._index_min = minute_index
                
            if not self._index_max or self._index_max < minute_index:
                self._index_max = minute_index

        self._minutes[minute_index].add(_app)

        self._sort()

        # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.layoutChanged.emit()

    def is_active(self, minute):
        if minute in self._minutes:
            return True
        return False

    def is_private(self, minute):
        if minute not in self._minutes:
            return False
        # print("%d: %s" %
        #      (minute, str([global_app_categories[a]
        #                    for a in self._minutes[minute]._apps])))
        # print(' '.join(reversed(["(%d: %d)" % (s, m._category)
        #                for s, m in self._minutes.items()])))
        return self._minutes[minute]._category != 0


class time_tracker():
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self, parent):
        self._idle_current = 0
        self._max_minute = 0  # does not need to be highest minute index
        self._current_app_title = ""
        self._current_process_exe = ""
        self._user_is_active = True
        self._active_day = today_int()
        

        # -- persist
        self._applications = active_applications(parent)

    def __eq__(self, other):
        return False

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def load(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % today_str()
        # print(_file_name)
        try:
            with open(_file_name) as _file:
                _struct = json.load(_file)
        except IOError:
            if filename is not None:
                logging.warn('file "%s" does not exist' % filename)
            return

        self._applications.from_dict(_struct)


    def save(self, filename=None):
        _file_name = filename if filename else "track-%s.json" % today_str() 
        # print(_file_name)
        _app_data = self._applications.__data__()
        with open(_file_name, 'w') as _file:
            json.dump(_app_data, _file,
                      sort_keys=True) #, indent=4, separators=(',', ': '))
            
        _test_model = active_applications(None)
        _test_model.from_dict(_app_data)
        assert self._applications == _test_model
        

    def get_applications_model(self):
        return self._applications

    def update(self):
        try:
            _today = today_int()

            if self._active_day < _today:
                print("current minute is %d - it's midnight" % _current_minute)
                #midnight!
                self.save('track-log-%d.json' % self._active_day)
                self.clear()

            self._active_day = today_int()

            self._max_minute = minutes_since_midnight()

            self._user_is_active = True

            self._idle_current = idle.getIdleSec()
            self._current_app_title = applicationinfo.get_active_window_title()
            self._current_process_exe = applicationinfo.get_active_process_name()
            if self._idle_current > 10:
                self._user_is_active = False
                return

            _app = self._applications.update(
                        self._max_minute,
                        app_info(self._current_app_title, 
                                 self._current_process_exe))

        except applicationinfo.UncriticalException as e:
            pass

    def begin_index(self):
        return self._applications.begin_index()

    def start_time(self):
        _s = self._applications.begin_index()
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def now(self):
        _s = self._max_minute
        return("%0.2d:%0.2d" % (int(_s/60), _s % 60))

    def is_active(self, minute):
        return self._applications.is_active(minute)

    def is_private(self, minute):
        return self._applications.is_private(minute)

    def get_time_total(self):
        return self._max_minute - self._applications.begin_index() + 1

    def get_time_active(self):
        return len(self._applications._minutes)

    def get_time_work(self):
        r = 0
        for i, m in self._applications._minutes.items():
            r += 1 if m._category == 0 else 0
        return r

    def get_time_private(self):
        r = 0
        for i, m in self._applications._minutes.items():
            r += m._category != 0
        return r

    def get_time_idle(self):
        return self.get_time_total() - len(self._applications._minutes)

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

