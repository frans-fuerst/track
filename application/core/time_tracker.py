#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines TimeTracker class which gathers and provides information about deskopt usage
"""

import json
import os
from typing import Any, Dict, Sequence, Tuple  # pylint: disable=unused-import

from . import common, ActiveApplications, Category
from ..core.util import catch, log, exception_to_string
from ..core import desktop_usage_info


class TimeTracker:
    """ * retrieves system data
        * holds the application data object as
          well as some meta information
        * provides persistence
    """
    def __init__(self, data_dir) -> None:
        self._idle_current = 0
        self._current_minute = 0  # does not need to be highest minute index
        self._current_app_title = ""
        self._current_process_exe = ""
        self._current_category = 0
        self._user_is_active = True
        self._active_day = common.today_int()
        self._storage_dir = data_dir

        # -- data to persist
        data = catch(
            lambda: self._load_json("track-%s.json" % common.today_str()),
            (FileNotFoundError, json.JSONDecodeError),
            {})
        self._applications = ActiveApplications(data.get("tracker_data"))
        self.note = data.get("daily_note")

        self._re_rules = catch(
            lambda: self._load_json("category_rules.json"),
            (FileNotFoundError, json.JSONDecodeError),
            [
                (r"check_mk", 2),
                (r".*Zoom.*", 2),
                (r"^Slack", 2),
                (r"^su heute", 2),
                (r"^Signal", 3),
                (r"^Zimbra", 2),
                (r"^gerrit/cmk", 2),
                (r"\[Jenkins\]", 2),
                (r"Track", 2),
                (r"^DER SPIEGEL", 3),
                (r".*SZ.de", 3),
            ])
        common.recategorize(self._applications.apps(), self._re_rules)

    def _load_json(self, filename: str) -> Any:
        """Properly read data from a JSON file"""
        with open(os.path.join(self._storage_dir, filename)) as file:
            return json.load(file)

    def _save_json(self, data, filename):
        """Properly write data to a JSON file"""
        os.makedirs(self._storage_dir, exist_ok=True)
        with open(os.path.join(self._storage_dir, filename), 'w') as file:
            json.dump(
                data,
                file,
                sort_keys=True,
                indent=4,
            )

    def __eq__(self, other):
        return False

    def clear(self) -> None:
        """Clear the application store - keeps the instance"""
        self._applications.clear()

    def persist(self, filename: str = None) -> None:
        """Store tracking info and regex rules on file system"""
        self._save_json(
            {"tracker_data": self._applications.__data__(),
             "daily_note": self.note},
            filename or "track-%s.json" % common.today_str())

        _test_model = ActiveApplications()
        _test_model.from_dict(self._applications.__data__())
        assert self._applications == _test_model
        self._save_json(self._re_rules, "category_rules.json")

    def get_applications_model(self) -> ActiveApplications:
        """Return the current application store"""
        return self._applications

    def rules(self) -> Sequence[Tuple[str, int]]:
        """Return the current set of regex rules"""
        return self._re_rules

    def set_rules(self, rules) -> None:
        """Store a new set of regex rules and recalculate categories"""
        self._re_rules = rules
        common.recategorize(self._applications.apps(), self._re_rules)

    def set_note(self, note) -> None:
        """Store daily note"""
        self.note = note

    def update(self) -> None:
        """Gather desktop usage info"""
        try:
            current_day = common.today_int()
            current_minute = common.minutes_since_midnight()

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

            app = common.AppInfo(self._current_app_title, self._current_process_exe)
            self._current_category = common.get_category(app, self._re_rules)
            app.set_category(self._current_category)
            self._applications.update(self._current_minute, app)
        except KeyError as exc:
            log().error("%r", _app_info)
            log().error("Got exception %r", exception_to_string(exc))
        except desktop_usage_info.WindowInformationError:
            pass
        except desktop_usage_info.ToolError as exc:
            log().error(exc)

    def current_state(self) -> Dict[str, Any]:
        """Retrieve current usage snapshot"""
        return {
            'minute': self._current_minute,
            'category': self._current_category,
            'time_total': self._current_minute - self._applications.begin_index() + 1,
            'user_idle': self._idle_current,
            'user_active': self._user_is_active,
            'app_title': self._current_app_title,
            'process_name': self._current_process_exe,
        }
