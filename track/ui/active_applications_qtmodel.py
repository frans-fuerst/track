#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""Defines ActiveApplicationsModel
"""

from typing import Any, Dict, Tuple  # pylint: disable=unused-import

from PyQt5 import QtCore

from ..core import ActiveApplications, common
from .qt_common import change_emitter


class ActiveApplicationsModel(QtCore.QAbstractTableModel, ActiveApplications):
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
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        ActiveApplications.__init__(self)
        self._sorted_keys = []
        self._sort_column = 1
        self._sort_order = QtCore.Qt.DescendingOrder

    def columnCount(self, _parent=None):
        return 3

    def rowCount(self, _parent=None):
        return len(self._sorted_keys)

    def headerData(self, column, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ("Application title", "Spent", "Category")[column]
        return None

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
            (self._apps[self._sorted_keys[row]]._wndtitle)
            if column == 0
            else common.secs_to_dur(self._apps[self._sorted_keys[row]]._count)
            if column == 1
            else self._apps[self._sorted_keys[row]]._category
        )

    def flags(self, _index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

    def sort(self, column=1, order=QtCore.Qt.DescendingOrder):
        """Called by the view on header clicks - remember the choice so that the
        per-second from_dict() refresh keeps it"""
        self._sort_column, self._sort_order = column, order
        key = (
            (lambda x: x[1]._wndtitle)
            if column == 0
            else (lambda x: x[1]._count)
            if column == 1
            else (lambda x: x[1]._category)
        )
        with change_emitter(self):
            self._sorted_keys = [
                app_id
                for app_id, _ in sorted(
                    self._apps.items(), key=key, reverse=(order == QtCore.Qt.DescendingOrder)
                )
            ]

    def clear(self):
        with change_emitter(self):
            super().clear()

    def from_dict(self, data: Dict[str, Any]) -> None:
        with change_emitter(self):
            super().from_dict(data)
            self.sort(self._sort_column, self._sort_order)

    def update(self, minute_index, app):
        with change_emitter(self):
            super().update(minute_index, app)
            self.sort(self._sort_column, self._sort_order)
