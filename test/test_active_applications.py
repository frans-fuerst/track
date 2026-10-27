#!/usr/bin/env python3
"""Unit tests for the core data model"""

import pytest

from track.core import ActiveApplications, AppInfo, Category, common

pytestmark = pytest.mark.unit


def filled_model() -> ActiveApplications:
    apps = ActiveApplications()
    for minute, title in ((0, "midnight"), (0, "midnight"), (1, "other"), (3, "midnight")):
        apps.update(minute, AppInfo(title, "cmd"))
    return apps


def test_empty_model_is_harmless():
    apps = ActiveApplications()
    assert str(apps) == "Apps(empty)"
    apps.clip_from(10)
    apps.clip_to(20)
    assert (apps.begin_index(), apps.end_index()) == (0, 0)
    assert apps.get_chunk_size(5) == (0, 0)


def test_minute_zero_is_a_valid_index():
    apps = filled_model()
    assert (apps.begin_index(), apps.end_index()) == (0, 3)
    assert apps.is_active(0)
    assert apps.info_at(0)[1].generate_identifier() == "midnight"


def test_round_trip():
    apps = filled_model()
    assert ActiveApplications(apps.__data__()) == apps


def test_clip():
    apps = filled_model()
    apps.clip_from(1)
    assert (apps.begin_index(), apps.end_index()) == (1, 3)
    apps.clip_to(1)
    assert (apps.begin_index(), apps.end_index()) == (1, 1)
    apps.clip_from(99)
    assert (apps.begin_index(), apps.end_index()) == (0, 0)


def test_get_category_ignores_case():
    rules = [("^slack", Category.WORK)]
    assert common.get_category(AppInfo("Slack - general"), rules) == Category.WORK
    assert common.get_category(AppInfo("Firefox"), rules) == Category.UNASSIGNED


def test_log_file_date():
    assert common.log_file_date("/some/dir/track-20200503.json") == "20200503"
    assert common.log_file_date("track-20200503.json.corrupt") is None
    assert common.log_file_date("category_rules.json") is None
