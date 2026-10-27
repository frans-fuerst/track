#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines TimeTracker class which gathers and provides information about deskopt usage
"""

import json
import os
import threading
from typing import Any, Dict, Optional, Sequence, Tuple  # pylint: disable=unused-import

from ..core import desktop_usage_info
from ..core.util import catch, exception_to_string, log
from . import ActiveApplications, common

DEFAULT_RULES = [
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
]


class TimeTracker:
    """* retrieves system data
    * holds the application data object as
      well as some meta information
    * provides persistence

    update() runs on the sampler thread while the request handlers read and
    serialize on the main thread, so every access to the application store
    goes through self._lock.
    """

    def __init__(self, data_dir: str) -> None:
        self._last_day = common.today_int()
        self._storage_dir = data_dir
        self._current_state = {}  # type: Dict[str, Any]
        self._lock = threading.Lock()

        # -- data to persist
        data = catch(
            lambda: self._load_json("track-%s.json" % common.today_str()), FileNotFoundError, {}
        )
        self._applications = ActiveApplications(data.get("tracker_data"))
        self.note = data.get("daily_note")
        log().info("Found app data: %r", self._applications)

        self._re_rules = catch(
            lambda: self._load_json("category_rules.json"), FileNotFoundError, DEFAULT_RULES
        )
        common.recategorize(self._applications.apps(), self._re_rules)

    def _load_json(self, filename: str) -> Any:
        """Read JSON from @filename. A corrupt file is moved aside (instead of being
        overwritten on the next save) and reported as missing"""
        path = os.path.join(self._storage_dir, filename)
        try:
            with open(path) as file:
                return json.load(file)
        except json.JSONDecodeError as exc:
            log().error("%s is corrupt (%s) - moved to %s.corrupt", path, exc, path)
            os.replace(path, path + ".corrupt")
            raise FileNotFoundError(path) from exc

    def _save_json(self, data: Any, filename: str) -> None:
        """Properly write data to a JSON file"""
        os.makedirs(self._storage_dir, exist_ok=True)
        with open(os.path.join(self._storage_dir, filename), "w") as file:
            json.dump(data, file, sort_keys=True, indent=4)

    def clear(self) -> None:
        """Clear the application store - keeps the instance"""
        with self._lock:
            self._applications.clear()

    def persist(self, filename: str) -> None:
        """Store tracking info and regex rules on file system"""
        log().info("Save tracker data to %r", filename)
        with self._lock:
            self._save_json(
                {"tracker_data": self._applications.__data__(), "daily_note": self.note}, filename
            )
            self._save_json(self._re_rules, "category_rules.json")

    def get_applications_model(self) -> ActiveApplications:
        """Return the current application store"""
        return self._applications

    def applications_data(self) -> Dict[str, Any]:
        """Serialized snapshot of the application store"""
        with self._lock:
            return self._applications.__data__()

    def clip_from(self, index: int) -> None:
        with self._lock:
            self._applications.clip_from(index)

    def clip_to(self, index: int) -> None:
        with self._lock:
            self._applications.clip_to(index)

    def rules(self) -> common.Rules:
        """Return the current set of regex rules"""
        return self._re_rules

    def set_rules(self, rules: common.Rules) -> None:
        """Store a new set of regex rules and recalculate categories"""
        with self._lock:
            self._re_rules = rules
            common.recategorize(self._applications.apps(), self._re_rules)

    def set_note(self, note: str) -> None:
        """Store daily note"""
        self.note = note

    def update(self) -> None:
        """Gather desktop usage info"""
        try:
            current_day, current_minute = common.today_int(), common.minutes_since_midnight()

            if current_day > self._last_day:
                log().info("current minute is %d - it's midnight", current_minute)
                self.persist("track-%d.json" % self._last_day)
                with self._lock:
                    self._applications.clear()
                    self.note = ""

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

            if user_is_active:
                with self._lock:
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
