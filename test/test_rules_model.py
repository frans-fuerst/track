#!/usr/bin/env python3
"""Unit tests for RulesModelQt (a bare model needs no QApplication)"""

import pytest
from PyQt5 import QtCore

from track.ui.rules_model_qt import RulesModelQt

pytestmark = pytest.mark.unit


def regexes(model: RulesModelQt):
    return [regex for regex, _ in model.rules()]


def test_move_rows():
    model = RulesModelQt(rules=[["a", 2], ["b", 3], ["c", 1]])
    assert model.moveRow(QtCore.QModelIndex(), 0, QtCore.QModelIndex(), 2)
    assert regexes(model) == ["b", "c", "a"]
    assert model.moveRow(QtCore.QModelIndex(), 2, QtCore.QModelIndex(), 0)
    assert regexes(model) == ["a", "b", "c"]
    assert not model.moveRow(QtCore.QModelIndex(), 1, QtCore.QModelIndex(), 1)


def test_set_data():
    model = RulesModelQt(rules=[["a", 2]])
    assert not model.setData(model.index(0, 0), "x(", QtCore.Qt.EditRole)
    assert not model.setData(model.index(0, 0), "x", QtCore.Qt.DisplayRole)
    assert model.setData(model.index(0, 0), "^x", QtCore.Qt.EditRole)
    assert model.setData(model.index(0, 1), "3", QtCore.Qt.EditRole)
    assert model.rules() == [["^x", 3]]
    # editing the trailing "new rule" row appends a rule
    assert model.setData(model.index(1, 0), "^y", QtCore.Qt.EditRole)
    assert regexes(model) == ["^x", "^y"]
