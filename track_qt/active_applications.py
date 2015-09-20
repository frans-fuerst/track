#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4 import QtCore #, Qt, uic, QtGui
from PyQt4.QtCore import pyqtSlot
#import json
#import operator
#import re

#from desktop_usage_info import idle
#from desktop_usage_info import applicationinfo
import track_common
import qt_common
import track_qt

# todo: separate qt model
class active_applications(qt_common.matrix_table_model):
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
        track_qt.matrix_table_model.__init__(self, parent, *args)
        self.header = ['application title', 'time', 'category']
        self._index_min = None
        self._index_max = None
        self._sorted_keys = []
        
        # to be persisted
        self._apps = {}     # app identifier => app_info instance
        self._minutes = {}  # i_min          => minute

    def clear(self):
        with track_qt.change_emitter(self):
            self._index_min = None
            self._index_max = None
            self._apps = {}     # app identifier => app_info instance
            self._minutes = {}  # i_min          => minute

    def rowCount(self, parent=None):
        return len(self._sorted_keys)

    def columnCount(self, parent):  # const
        return 3

    def _data(self, row, column):  # const
        if column == 0:
            return self._apps[self._sorted_keys[row]]._wndtitle
        elif column == 1:
            return track_common.secs_to_dur(self._apps[self._sorted_keys[row]]._count)
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
        _indexed = [track_common.app_info().load(d) for d in _a]
        _m = data['minutes']
        _minutes = {
            int(i) : track_common.minute().init(
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
        with track_qt.change_emitter(self):

            self._apps = _apps
            self._minutes = _minutes

            if len(self._minutes) > 0:
                self._index_min = min(self._minutes.keys())
                self._index_max = max(self._minutes.keys())
            else:
                self._index_min = None
                self._index_max = None
                
            self._sort()
        
        # print(_minutes)
    
    def begin_index(self):  # const
        return self._index_min if self._index_min else 0

    def end_index(self):  # const
        return self._index_max if self._index_max else 0

    def update(self, minute_index, app):
        with track_qt.change_emitter(self):
            _app_id = app.generate_identifier()
            if _app_id not in self._apps:
                self._apps[_app_id] = app
            _app = self._apps[_app_id]
            _app.set_new_category(app.get_category())
            _app._count += 1 #seconds using the app
            if minute_index not in self._minutes:
                self._minutes[minute_index] = track_common.minute()
                if not self._index_min or self._index_min > minute_index:
                    self._index_min = minute_index
                    
                if not self._index_max or self._index_max < minute_index:
                    self._index_max = minute_index

            self._minutes[minute_index].add(_app)

            self._sort()
            
            # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def get_chunk_size(self, minute):
        _begin = minute
        _end = minute

        if minute > self._index_max or minute < self._index_min:
            return (_begin, _end)

        if self.is_active(minute):
            _a = self._minutes[minute].get_main_app()
        else:
            _a = None

        _minutes = sorted(self._minutes.keys())

        _lower_range = [i for i in _minutes if i < minute]
        _upper_range = [i for i in _minutes if i > minute]

        if _a is None:
            _begin = _lower_range[-1] if _lower_range != [] else _begin
            _end = _upper_range[0] if _upper_range != [] else _end
            return (_begin, _end)

        # print(len(_minutes))

        # print(minute)
        # print(_i)
        # print(_minutes[_minutes.index(minute)])
        # print(list(reversed(range(_i))))
        for i in reversed(_lower_range):
            if _begin - i > 1:
                break
            if self._minutes[i].get_main_app() == _a:
                _begin = i

        # print(list(range(_i + 1, len(_minutes))))
        for i in _upper_range:
            if i - _end > 1:
                break
            if self._minutes[i].get_main_app() == _a:
                _end = i

        # todo: currently gap is max 1min - make configurable
        return (_begin, _end)

    def info(self, minute):
        if self.is_active(minute):
            _activity = str(self._minutes[minute].get_main_app())
        else:
            _activity = 'idle'
        
        _cs = self.get_chunk_size(minute)
        # print(mins_to_str(_cs[1]-_cs[0]) + " / " + str(_cs))
        return (_cs, _activity)

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
    @pyqtSlot()
    def update_all_categories(self, get_category_from_app):
        for i in self._apps:
            self._apps[i].set_new_category(get_category_from_app(self._apps[i]))
