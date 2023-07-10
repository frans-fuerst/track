#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines class ActiveApplications
"""

from typing import Any, Dict, Tuple  # pylint: disable=unused-import

from ..core import common


class ActiveApplications:
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

    def __init__(self, json_data=None):
        self.clear()

        if json_data is not None:
            self.from_dict(json_data)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "Apps(%r to %r)" % (
            common.mins_to_date(self._index_min),
            common.mins_to_date(self._index_max),
        )

    def clear(self):
        """Clears all data (app info and timeline)"""
        # todo: mutex
        self._index_min = None
        self._index_max = None
        self._apps = {}  # app identifier => AppInfo instance
        self._minutes = {}  # i_min          => minute

    def clip_from(self, index):
        """Removes all timeline data before provided index"""
        self._minutes = {minute: apps for minute, apps in self._minutes.items() if minute >= index}
        self._index_min = min(self._minutes.keys())

    def clip_to(self, index):
        """Removes all timeline data after provided index"""
        self._minutes = {minute: apps for minute, apps in self._minutes.items() if minute <= index}
        self._index_max = max(self._minutes.keys())

    def __eq__(self, other):
        """Comparing is only needed for tests"""
        if not self._apps == other._apps:
            return False
        if not self._minutes == other._minutes:
            if not self._minutes.keys() == other._minutes.keys:
                return False
            for key in self._minutes:
                if not self._minutes[key] == other._minutes[key]:
                    return False
        return True

    def __data__(self):  # const
        """we have to create an indexed list here because the minutes
        dict has to store references to AppInfo.
        intermediate: _indexed: {app_id => (i_index, AppInfo)}
        result:    app:     [AppInfo]
                   minutes: {i_minute: (i_category, [(AppInfo, i_count)])}

        """
        _indexed = {a: i for i, a in enumerate(self._apps.values())}
        _apps = [d[1] for d in sorted([(e[1], e[0].__data__()) for e in _indexed.items()])]
        _minutes = {
            i: [(_indexed[a], c) for a, c in m._app_counter.items()]
            for i, m in self._minutes.items()
        }
        return {"apps": _apps, "minutes": _minutes}

    def from_dict(self, data):
        def convert(minutes):
            # todo: just translate local files
            if all(len(data) == 2 and isinstance(data[0], int) for index, data in minutes.items()):
                return {key: value[1] for key, value in minutes.items()}
            return minutes

        assert "apps" in data
        assert "minutes" in data
        _a = data["apps"]
        _indexed = [common.AppInfo().load(d) for d in _a]
        _m = convert(data["minutes"])
        _minutes = {int(i): common.Minute({_indexed[a]: c for a, c in m}) for i, m in _m.items()}

        _apps = {a.generate_identifier(): a for a in _indexed}

        self._apps = _apps
        self._minutes = _minutes

        if len(self._minutes) > 0:
            self._index_min = min(self._minutes.keys())
            self._index_max = max(self._minutes.keys())
        else:
            self._index_min = None
            self._index_max = None

    def begin_index(self):  # const
        return self._index_min if self._index_min else 0

    def end_index(self):  # const
        return self._index_max if self._index_max else 0

    def update(self, minute_index, app):
        # todo: mutex
        _app_id = app.generate_identifier()

        if _app_id not in self._apps:
            self._apps[_app_id] = app

        _app = self._apps[_app_id]
        _app._count += 1

        if minute_index not in self._minutes:
            self._minutes[minute_index] = common.Minute()
            if not self._index_min or self._index_min > minute_index:
                self._index_min = minute_index

            if not self._index_max or self._index_max < minute_index:
                self._index_max = minute_index

        self._minutes[minute_index].add(_app)

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
            return (
                _lower_range[-1] if _lower_range != [] else _begin,
                _upper_range[0] if _upper_range != [] else _end,
            )

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

    def info_at(self, minute: int) -> Tuple[int, str]:
        return (
            self.get_chunk_size(minute),
            self._minutes[minute].main_app() if self.is_active(minute) else "idle",
        )

    def is_active(self, minute):
        return minute in self._minutes

    def category_at(self, minute):
        return self._minutes[minute].main_category() if minute in self._minutes else 0

    def apps(self):
        return (app for _, app in self._apps.items())
