"""Focused window via the "Window Calls Extended" shell extension"""

from contextlib import suppress

import psutil

from .. import WindowInformationError
from . import gdbus_call


def _focus(what: str) -> str:
    return gdbus_call(
        "org.gnome.Shell",
        "/org/gnome/Shell/Extensions/WindowsExt",
        "org.gnome.Shell.Extensions.WindowsExt.Focus%s" % what,
    )[0]


def get_active_window_information():
    title = _focus("Title")
    if not title:
        raise WindowInformationError("no focused window")
    result = {"TITLE": title}
    with suppress(ValueError):
        result["PID"] = int(_focus("PID"))
    if "PID" in result:
        with suppress(psutil.Error):
            result["COMMAND"] = " ".join(psutil.Process(result["PID"]).cmdline())
    return result
