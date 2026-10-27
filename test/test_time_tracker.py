#!/usr/bin/env python3
"""Unit tests for TimeTracker persistence"""

import json

import pytest

from track.core import AppInfo, TimeTracker, common

pytestmark = pytest.mark.unit


def test_fresh_tracker(tmp_path):
    tracker = TimeTracker(data_dir=str(tmp_path))
    assert tracker.note is None
    assert tracker.applications_data() == {"apps": [], "minutes": {}}


def test_persist_round_trip(tmp_path):
    filename = "track-%s.json" % common.today_str()
    tracker = TimeTracker(data_dir=str(tmp_path))
    tracker.get_applications_model().update(5, AppInfo("a", "b"))
    tracker.set_note("hello")
    tracker.set_rules([["^a", 3]])
    tracker.persist(filename)

    reloaded = TimeTracker(data_dir=str(tmp_path))
    assert reloaded.note == "hello"
    assert reloaded.rules() == [["^a", 3]]
    assert reloaded.get_applications_model() == tracker.get_applications_model()
    assert next(reloaded.get_applications_model().apps())._category == 3


def test_corrupt_file_is_kept(tmp_path):
    filename = "track-%s.json" % common.today_str()
    (tmp_path / filename).write_text("{not json")
    tracker = TimeTracker(data_dir=str(tmp_path))
    assert (tmp_path / (filename + ".corrupt")).read_text() == "{not json"
    tracker.persist(filename)
    assert json.loads((tmp_path / filename).read_text())["tracker_data"]["minutes"] == {}
