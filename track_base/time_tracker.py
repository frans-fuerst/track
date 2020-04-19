#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
import re
from typing import Any
log = logging.getLogger('base.time_tracker')

import desktop_usage_info

from track_base import ActiveApplications
from track_base import track_common
import track_base

from track_base import catch

class TimeTracker:
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self):
        self._idle_current = 0
        self._current_minute = 0  # does not need to be highest minute index
        self._current_app_title = ""
        self._current_process_exe = ""
        self._current_category = 0
        self._user_is_active = True
        self._active_day = track_common.today_int()
        self._storage_dir = os.path.expanduser("~/.track")

        # -- data to persist
        data = catch(
            lambda: self.load_json("track-%s.json" % track_common.today_str()),
            (FileNotFoundError, json.JSONDecodeError),
            {})
        self._applications = ActiveApplications(data.get("tracker_data"))
        self.note = data.get("daily_note")

        self._re_rules = catch(
            lambda: self.load_json("category_rules.json"),
            (FileNotFoundError, json.JSONDecodeError),
            [
                ("check_mk", 2),
                (".*Zoom.*",2),
                ("^Slack", 2),
                ("^su heute", 2),
                ("^Signal", 3),
                ("^Zimbra", 2),
                ("^gerrit/cmk", 2),
                ("\[Jenkins\]", 2),
                ("Track", 2),
                ("^DER SPIEGEL", 3),
                (".*SZ.de", 3),
            ])
        self._recategorize()

    def get_category(self, app):
        app_string_representation = app.generate_identifier()
        for rule, category in self._re_rules:
            if re.search(rule, app_string_representation):
                return category
        return track_common.Category.UNASSIGNED

    def _recategorize(self):
        for title, app in self._applications._apps.items():
            app._category = self.get_category(app)

    def load_json(self, filename: str) -> Any:
        with open(os.path.join(self._storage_dir, filename)) as file:
            return json.load(file)

    def save_json(self, data, filename):
        os.makedirs(self._storage_dir, exist_ok=True)
        with open(os.path.join(self._storage_dir, filename), 'w') as file:
            json.dump(
                data,
                file,
                sort_keys=True,
                indent=4,
                #separators=(',', ': '),
            )

    def __eq__(self, other):
        return False

    def clear(self):
        # must not be overwritten - we need the instance
        self._applications.clear()

    def persist(self, filename=None):
        self.save_json({
            "tracker_data": self._applications.__data__(),
            "daily_note": self.note},
            filename or "track-%s.json" % track_common.today_str())

        _test_model = ActiveApplications()
        _test_model.from_dict( self._applications.__data__())
        assert self._applications == _test_model
        self.save_json(self._re_rules, "category_rules.json")

    def get_applications_model(self):
        return self._applications

    def rules(self):
        return self._re_rules

    def set_rules(self, rules):
        self._re_rules = rules
        self._recategorize()

    def set_note(self, note):
        self.note = note

    def update(self):
        try:
            current_day = track_common.today_int()
            current_minute = track_common.minutes_since_midnight()

            if self._active_day < current_day:
                print("current minute is %d - it's midnight" % self._current_minute)
                self.persist('track-log-%d.json' % self._active_day)
                self.clear()

            self._active_day = current_day
            self._current_minute = current_minute

            self._user_is_active = True

            self._idle_current = int(desktop_usage_info.idle.getIdleSec())
            _app_info = desktop_usage_info.applicationinfo.get_active_window_information()

            self._current_app_title = _app_info["TITLE"]
            self._current_process_exe = _app_info.get("COMMAND", "Process not found")

            if self._idle_current > 10:
                self._user_is_active = False
                return

            _app = track_common.AppInfo(self._current_app_title, self._current_process_exe)
            self._current_category = self.get_category(_app)
            _app._category = self._current_category
            _app = self._applications.update(self._current_minute, _app)

        except desktop_usage_info.WindowInformationError:
            pass
        except desktop_usage_info.ToolError as ex:
            log.error(ex)

    def get_current_data(self):
        return {
            'minute': self._current_minute,
            'category': self._current_category,
            'time_total': self._current_minute - self._applications.begin_index() + 1,
            'user_idle': self._idle_current,
            'user_active': self._user_is_active,
            'app_title': self._current_app_title,
            'process_name': self._current_process_exe,
        }
