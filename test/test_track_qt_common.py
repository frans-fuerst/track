#!/usr/bin/env python3
"""Unit tests for shared Qt helpers"""

import pytest
from PyQt5 import QtCore

from track.core import Category
from track.ui.qt_common import CategoryColor, change_emitter

pytestmark = pytest.mark.unit


class Signal:
    def __init__(self):
        self.count = 0

    def emit(self):
        self.count += 1


class Emitter:
    def __init__(self):
        self.layoutAboutToBeChanged = Signal()
        self.layoutChanged = Signal()


def test_change_emitter():
    emitter = Emitter()
    with change_emitter(emitter):
        assert (emitter.layoutAboutToBeChanged.count, emitter.layoutChanged.count) == (1, 0)
    assert (emitter.layoutAboutToBeChanged.count, emitter.layoutChanged.count) == (1, 1)


def test_category_color_known_for_all_categories():
    assert CategoryColor(99) == QtCore.Qt.red
    assert all(CategoryColor(category) != QtCore.Qt.red for category in Category)
