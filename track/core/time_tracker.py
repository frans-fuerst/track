#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines TimeTracker class which gathers and provides information about deskopt usage
"""

import json
import os
from typing import Any, Dict, Optional, Sequence, Tuple  # pylint: disable=unused-import

from ..core import desktop_usage_info
from ..core.util import catch, exception_to_string, log
from . import ActiveApplications, common


class TimeTracker:
    """* retrieves system data
    * holds the application data object as
      well as some meta information
    * provides persistence
    """

    def __init__(self, data_dir: str) -> None:
        self._last_day = common.today_int()
        self._storage_dir = data_dir
        self._current_state = {}  # type: Dict[str, Any]

        # -- data to persist
        data = catch(
            lambda: self._load_json("track-%s.json" % common.today_str()),
            (FileNotFoundError, json.JSONDecodeError),
            {},
        )
        self._applications = ActiveApplications(data.get("tracker_data"))
        self.note = data.get("daily_note")
        log().info("Found app data: %r", self._applications)

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
            ],
        )
        common.recategorize(self._applications.apps(), self._re_rules)

    def _load_json(self, filename: str) -> Any:
        """Properly read data from a JSON file"""
        with open(os.path.join(self._storage_dir, filename)) as file:
            return json.load(file)

    def _save_json(self, data: Dict[str, Any], filename: str) -> None:
        """Properly write data to a JSON file"""
        os.makedirs(self._storage_dir, exist_ok=True)
        with open(os.path.join(self._storage_dir, filename), "w") as file:
            json.dump(
                data,
                file,
                sort_keys=True,
                indent=4,
            )

    def __eq__(self, other: object) -> bool:
        return False

    def clear(self) -> None:
        """Clear the application store - keeps the instance"""
        self._applications.clear()

    def persist(self, filename: str) -> None:
        """Store tracking info and regex rules on file system"""
        log().info("Save tracker data to %r", filename)
        self._save_json(
            {"tracker_data": self._applications.__data__(), "daily_note": self.note}, filename
        )
        self._save_json(self._re_rules, "category_rules.json")

        # just for development
        _test_model = ActiveApplications()
        _test_model.from_dict(self._applications.__data__())
        assert self._applications == _test_model

    def get_applications_model(self) -> ActiveApplications:
        """Return the current application store"""
        return self._applications

    def rules(self) -> common.Rules:
        """Return the current set of regex rules"""
        return self._re_rules

    def set_rules(self, rules: common.Rules) -> None:
        """Store a new set of regex rules and recalculate categories"""
        self._re_rules = rules
        common.recategorize(self._applications.apps(), self._re_rules)

    def set_note(self, note: str) -> None:
        """Store daily note"""
        self.note = note

    def update(self) -> None:
        """Gather desktop usage info"""
        try:
            current_day, current_minute = common.today_int(), common.minutes_since_midnight()
            midnight = current_day > self._last_day

            if midnight:
                log().info("current minute is %d - it's midnight", current_minute)
                self.persist("track-backup-%d.json" % self._last_day)
                self.clear()

            self._last_day = current_day

            app_info = desktop_usage_info.applicationinfo.get_active_window_information()
            current_app_title = app_info["TITLE"]
            current_process_exe = app_info.get("COMMAND", "Process not found")
            app = common.AppInfo(current_app_title, current_process_exe)
            current_category = common.get_category(app, self._re_rules)
            app.set_category(current_category)

            idle_current = desktop_usage_info.idle.getIdleSec()
            user_is_active = idle_current <= 10

            self._current_state = {
                "minute": current_minute,
                "category": current_category,
                "time_total": current_minute - self._applications.begin_index() + 1,
                "user_idle": idle_current,
                "user_active": user_is_active,
                "app_title": current_app_title,
                "process_name": current_process_exe,
            }
            print(self._current_state)

            if user_is_active:
                self._applications.update(current_minute, app)

        except KeyError as exc:
            log().error("%r", app_info)
            log().error("Got exception %r", exception_to_string(exc))
        except desktop_usage_info.WindowInformationError:
            pass
        except desktop_usage_info.ToolError as exc:
            log().error(exc)

    def current_state(self) -> Dict[str, Any]:
        """Retrieve current usage snapshot"""
        return self._current_state
