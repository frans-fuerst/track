#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""Defines ActiveApplicationsModel
"""

from typing import Any, Tuple, Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot

import track_qt
import track_base

from track_qt.qt_common import matrix_table_model


class ActiveApplicationsModel(matrix_table_model):
    """Data model which holds all application usage data for one
        day. That is:

        app_data:  {app_id: application}

        minutes:   {i_min => [app_id], i_cat}

        where

        application:  (i_secs, i_cat, s_title, s_process)


        model_list:
            * sortable by key
            * can be done with list of keys sorted by given value
            [(app_id, i_secs, i_cat)]
    """
    def __init__(self, parent, *args) -> None:
        super().__init__(parent, *args)
        self.header = ['Application title', 'Spent', 'Category']
        self._index_min = None
        self._index_max = None
        self._sort_column = 1
        self._sort_reverse = True
        self._sorted_keys = []

        # to be persisted
        self._apps = {}     # app identifier => AppInfo instance
        self._minutes = {}  # i_min          => minute

    def clear(self):
        with track_qt.change_emitter(self):
            self._index_min = None
            self._index_max = None
            self._apps = {}     # app identifier => AppInfo instance
            self._minutes = {}  # i_min          => minute

    def rowCount(self, parent=None):
        return len(self._sorted_keys)

    def columnCount(self, parent):  # const
        return 3

    def data(self, index, role):
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if column == 2:
                return QtCore.Qt.AlignCenter
        if not role == QtCore.Qt.DisplayRole:
            return None
        return (
            self._apps[self._sorted_keys[row]]._wndtitle if column == 0 else
            track_base.secs_to_dur(self._apps[self._sorted_keys[row]]._count) if column == 1 else
            self._apps[self._sorted_keys[row]]._category if column == 2 else
            throw(IndexError))

    def __eq__(self, other):
        return self._apps == other._apps and self._minutes == other._minutes

    def _sort(self):
        self._sorted_keys = [
            x[0] for x in sorted(
                self._apps.items(),
                key=((lambda x: x[1]._wndtitle) if self._sort_column == 0 else
                     (lambda x: x[1]._count) if self._sort_column == 1 else
                     (lambda x: x[1]._category)),
                reverse=self._sort_reverse)]

    #def __data__(self):  # const
        #""" we have to create an indexed list here because the minutes
            #dict has to store references to AppInfo.
            #intermediate: _indexed: {app_id => (i_index, AppInfo)}
            #result:    app:     [AppInfo]
                       #minutes: {i_minute: (i_category, [(AppInfo, i_count)])}

            #"""
        #_indexed = {a: i for i, a in enumerate(self._apps.values())}
        #_apps = [d[1] for d in sorted([(e[1], e[0].__data__())
                                       #for e in _indexed.items()])]
        #_minutes = {i: (m._category, [(_indexed[a], c)
                                      #for a, c in m._apps.items()])
                    #for i, m in self._minutes.items()}

        #return {"apps": _apps, 'minutes': _minutes}

    def from_dict(self, data: Dict[str, Any]) -> None:
        assert 'apps' in data
        assert 'minutes' in data
        _a = data['apps']
        _indexed = [track_base.AppInfo().load(d) for d in _a]

        _m = data['minutes']
        _minutes = {int(i) : track_base.Minute({_indexed[a]: c for a, c in m})
                    for i, m in _m.items()}

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

    def begin_index(self):
        return self._index_min if self._index_min else 0

    def end_index(self):
        return self._index_max if self._index_max else 0

    def update(self, minute_index, app):
        with track_qt.change_emitter(self):
            _app_id = app.generate_identifier()

            if _app_id not in self._apps:
                self._apps[_app_id] = app

            _app = self._apps[_app_id]
            _app._count += 1

            if minute_index not in self._minutes:
                self._minutes[minute_index] = track_base.Minute()
                if not self._index_min or self._index_min > minute_index:
                    self._index_min = minute_index

                if not self._index_max or self._index_max < minute_index:
                    self._index_max = minute_index

            self._minutes[minute_index].add(_app)

            self._sort()

            # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def get_chunk_size(self, minute):
        if not (self._index_max and self._index_min):
            return 0, 0

        _begin = minute
        _end = minute

        if minute > self._index_max or minute < self._index_min:
            return _begin, _end

        _a = self._minutes[minute].main_app() if self.is_active(minute) else None
        _minutes = sorted(self._minutes.keys())
        _lower_range = [i for i in _minutes if i < minute]
        _upper_range = [i for i in _minutes if i > minute]

        if _a is None:
            return (_lower_range[-1] if _lower_range != [] else _begin,
                    _upper_range[0] if _upper_range != [] else _end)

        for i in reversed(_lower_range):
            if _begin - i > 1:
                break
            if self._minutes[i].main_app() == _a:
                _begin = i

        for i in _upper_range:
            if i - _end > 1:
                break
            if self._minutes[i].main_app() == _a:
                _end = i

        # todo: currently gap is max 1min - make configurable
        return _begin, _end

    def info(self, minute: int) -> Tuple[int, str]:
        return (self.get_chunk_size(minute),
                self._minutes[minute].main_app() if self.is_active(minute) else "idle")

    def is_active(self, minute):
        return minute in self._minutes

    def category_at(self, minute):
        return self._minutes[minute].main_category() if minute in self._minutes else 0

    @pyqtSlot()
    def update_all_categories(self, get_category_from_app) -> None:
        for i in self._apps:
            self._apps[i].set_new_category(get_category_from_app(self._apps[i]))
        for i in self._minutes:
            self._minutes[i].rebuild_categories(get_category_from_app)

    def flags(self, index):
        return (QtCore.Qt.ItemIsEnabled |
                QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsDragEnabled)

