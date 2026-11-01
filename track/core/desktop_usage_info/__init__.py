"""Active window title/PID and idle time, with one backend per desktop
environment. Every backend provides

    applicationinfo.get_active_window_information() -> {"TITLE", "PID"?, "COMMAND"?}
    idle.getIdleSec() -> int
"""

import importlib
import os


class TrackServerError(Exception):
    pass


class WindowInformationError(TrackServerError):
    pass


class ToolError(TrackServerError):
    pass


def backend_name(environ=os.environ) -> str:
    """'windows', 'gnome' (GNOME Shell on Wayland) or 'x11'; TRACK_BACKEND overrides"""
    is_gnome_wayland = bool(environ.get("WAYLAND_DISPLAY")) and "GNOME" in environ.get(
        "XDG_CURRENT_DESKTOP", ""
    )
    return environ.get("TRACK_BACKEND") or (
        "windows" if os.name == "nt" else "gnome" if is_gnome_wayland else "x11"
    )


applicationinfo = importlib.import_module(".backend_%s.applicationinfo" % backend_name(), __name__)
idle = importlib.import_module(".backend_%s.idle" % backend_name(), __name__)
