#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines daily log visualizer classes
"""
import json
from datetime import datetime

from PyQt5 import QtWidgets, QtGui, QtCore

from ..core import common, ActiveApplications
from .qt_common import CategoryColor
from .qt_common import TimechartDataprovider


class FileDataprovider(TimechartDataprovider):
    """"""
    def __init__(self, filename):
        def convert(data):
            return data if "tracker_data" in data else {"tracker_data": data}

        with open(filename) as file:
            data = convert(json.load(file))
            self.apps = ActiveApplications(data["tracker_data"])
            self.daily_note = data.get("daily_note") or ""
        self._date = datetime.strptime(filename[-13:-5], "%Y%m%d")

    def date(self) -> datetime:
        return self._date

    def initialized(self):
        return True

    def current_minute(self) -> int:
        return self.end_index()

    def clip_from(self, index: str) -> None:
        pass

    def clip_to(self, index: int) -> None:
        pass

    def begin_index(self):
        return self.apps.begin_index()

    def end_index(self):
        return self.apps.end_index()

    def info_at(self, minute: int):
        return self.apps.info_at(minute)

    def category_at(self, minute: int):
        return self.apps.category_at(minute)

    def time_active(self):
        return len(self.apps._minutes)

    def time_work(self):
        return sum(minute.main_category() == 2 for _, minute in self.apps._minutes.items())

    def time_private(self):
        return sum(minute.main_category() == 3 for _, minute in self.apps._minutes.items())

    def time_total(self):
        return self.end_index() - self.begin_index()

    def time_idle(self):
        return self.time_total() - self.time_active()

    def recategorize(self, rules: common.Rules) -> None:
        common.recategorize(self.apps.apps(), rules)


class Timegraph(QtWidgets.QFrame):
    clipFromClicked = QtCore.pyqtSignal(int)
    clipToClicked = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dataprovider = None
        self.setMouseTracking(True)
        self._selected = None
        self.setMinimumHeight(50)

    def leaveEvent(self, _event):
        self.select()

    def set_dataprovider(self, dataprovider):
        self._dataprovider = dataprovider

    def dataprovider(self):
        return self._dataprovider

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._dataprovider is None:
            return

        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def mouseMoveEvent(self, event):
        if self._dataprovider is None:
            return
        _index = self._dataprovider.begin_index() - 50 + event.x() - 1
        _cs, _activity = self._dataprovider.info_at(_index)

        _info_str = "%s: %s (%s)" % (
            common.mins_to_dur(_index),
            _activity,
            common.mins_to_dur(_cs[1]-_cs[0]))
        self.select(_cs[0], _cs[1])
        self.setToolTip(_info_str)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        index = self._dataprovider.begin_index() - 50 + event.x() - 1
        clip_from = menu.addAction("clip before %s (erases data!)" % common.mins_to_dur(index))
        clip_to = menu.addAction("clip after %s (erases data!)" % common.mins_to_dur(index))
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == clip_from:
            self.clipFromClicked.emit(index)
        if action == clip_to:
            self.clipToClicked.emit(index)

    def drawPoints(self, qp):
        if not self._dataprovider.initialized():
            return

        _start_index = self._dataprovider.begin_index() - 50
        for i in range(self.width() - 2):
            _index = _start_index + i
            qp.setPen(
                # dark gray on borders of tracked time
                QtCore.Qt.gray if i < 50 or _index > self._dataprovider.current_minute() else
                # black 'now' line
                QtCore.Qt.black if self._dataprovider.current_minute() == _index else
                CategoryColor(self._dataprovider.category_at(_index)))

            qp.drawLine(i + 1, 0, i + 1, self.height() - 2)

        if self._selected is None:
            return

        qp.setPen(QtCore.Qt.blue)
        for i in range(self._selected[0], self._selected[1] + 1):
            qp.drawLine(i - _start_index, 0 + 20, i - _start_index, self.height() - 2 - 20)

    def select(self, begin=None, end=None):
        self._selected = (begin, end) if begin is not None and end is not None else None
        self.update()


class EvaluationWidget(QtWidgets.QFrame):
    def __init__(self, parent=None, *, dataprovider=None):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Box)
        layout1 = QtWidgets.QVBoxLayout()
        layout2 = QtWidgets.QHBoxLayout()
        layout3 = QtWidgets.QHBoxLayout()
        layout1.setContentsMargins(10, 2, 10, 0)
        layout2.setContentsMargins(0, 0, 0, 0)
        layout3.setContentsMargins(0, 0, 0, 0)

        self.timegraph = Timegraph()
        font = QtGui.QFont()
        font.setBold(True)

        self.lbl_date = QtWidgets.QLabel("Date")
        self.lbl_date.setFont(font)
        self.lbl_totals = QtWidgets.QLabel("Totals")
        self.lbl_totals.setFont(font)
        self.timegraph.clipFromClicked.connect(self.on_timegraph_clipFromClicked)
        self.timegraph.clipToClicked.connect(self.on_timegraph_clipToClicked)

        self.lbl_active = QtWidgets.QLabel("active")
        self.lbl_work = QtWidgets.QLabel("work")
        self.lbl_private = QtWidgets.QLabel("private")
        self.lbl_idle = QtWidgets.QLabel("idle")
        layout3.addWidget(self.lbl_active)
        layout3.addWidget(self.lbl_work)
        layout3.addWidget(self.lbl_private)
        layout3.addWidget(self.lbl_idle)

        layout2.addWidget(self.lbl_date)
        layout2.addWidget(self.lbl_totals)

        layout1.addLayout(layout2)
        layout1.addWidget(self.timegraph)
        layout1.addLayout(layout3)

        self.setLayout(layout1)
        if dataprovider is not None:
            self.set_dataprovider(dataprovider)

    @QtCore.pyqtSlot(int)
    def on_timegraph_clipFromClicked(self, index: int) -> None:
        self.timegraph.dataprovider().clip_from(index)

    @QtCore.pyqtSlot(int)
    def on_timegraph_clipToClicked(self, index: int) -> None:
        self.timegraph.dataprovider().clip_to(index)

    def set_dataprovider(self, dataprovider):
        self.timegraph.set_dataprovider(dataprovider)
        self.update_widgets()

    def update_widgets(self):
        def fmt(dur: int) -> str:
            return "%0.2d:%0.2d" % (int(dur // 60), dur % 60)

        dp = self.timegraph.dataprovider()
        self.lbl_date.setText(dp.date().strftime("%Y/%m/%d-%A"))
        _time_total = dp.time_total()
        _time_active = dp.time_active()
        _time_work = dp.time_work()
        _time_private = dp.time_private()
        _time_idle = dp.time_idle()
        percentage = 100. / _time_total if _time_total else 0.
        self.lbl_active.setText("active: %s (%d%%)" % (
            common.mins_to_dur(_time_active), _time_active * percentage))
        self.lbl_work.setText("work: %s (%d%%)" % (
            common.mins_to_dur(_time_work), _time_work * percentage))
        self.lbl_private.setText("private: %s (%d%%)" % (
            common.mins_to_dur(_time_private), _time_private * percentage))
        self.lbl_idle.setText("idle: %s (%d%%)" % (
            common.mins_to_dur(_time_idle), _time_idle * percentage))

        self.lbl_totals.setText("%s - %s: %s" % (
            fmt(dp.begin_index()),
            fmt(dp.current_minute()),
            common.mins_to_dur(_time_total)))

    def recategorize(self, rules: common.Rules):
        self.timegraph.dataprovider().recategorize(rules)
        self.timegraph.update()
