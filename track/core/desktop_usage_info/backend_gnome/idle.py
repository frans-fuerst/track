"""Idle time from Mutter's idle monitor"""

from . import gdbus_call


def getIdleSec() -> int:
    return (
        gdbus_call(
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor.GetIdletime",
        )[0]
        // 1000
    )
