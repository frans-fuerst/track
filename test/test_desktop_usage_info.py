#!/usr/bin/env python3
"""Unit tests for backend selection and the GNOME/Wayland backend's parsing"""

import subprocess

import psutil
import pytest

from track.core import desktop_usage_info
from track.core.desktop_usage_info import backend_gnome
from track.core.desktop_usage_info.backend_gnome import applicationinfo, idle

pytestmark = pytest.mark.unit


def test_backend_name():
    assert desktop_usage_info.backend_name({}) == "x11"
    assert desktop_usage_info.backend_name({"WAYLAND_DISPLAY": "wayland-0"}) == "x11"
    assert (
        desktop_usage_info.backend_name(
            {"WAYLAND_DISPLAY": "wayland-0", "XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}
        )
        == "gnome"
    )
    assert desktop_usage_info.backend_name({"TRACK_BACKEND": "gnome"}) == "gnome"


def fake_gdbus(monkeypatch, replies, returncode=0):
    """Let `gdbus call` answer from @replies, keyed by method name"""

    def run(args, **_kwargs):
        return subprocess.CompletedProcess(
            args, returncode, stdout=replies[args[-1].rsplit(".", 1)[-1]], stderr="nope"
        )

    monkeypatch.setattr(backend_gnome.subprocess, "run", run)


def test_idle(monkeypatch):
    fake_gdbus(monkeypatch, {"GetIdletime": "(uint64 32500,)\n"})
    assert idle.getIdleSec() == 32


def test_active_window(monkeypatch):
    fake_gdbus(monkeypatch, {"FocusTitle": "(\"it's - Firefox\",)\n", "FocusPID": "('4711',)\n"})
    def gone(pid):
        raise psutil.NoSuchProcess(pid)

    monkeypatch.setattr(applicationinfo.psutil, "Process", gone)
    info = applicationinfo.get_active_window_information()
    assert (info["TITLE"], info["PID"]) == ("it's - Firefox", 4711)
    assert "COMMAND" not in info


def test_no_focused_window(monkeypatch):
    fake_gdbus(monkeypatch, {"FocusTitle": "('',)\n"})
    with pytest.raises(desktop_usage_info.WindowInformationError):
        applicationinfo.get_active_window_information()


def test_gdbus_failure(monkeypatch):
    fake_gdbus(monkeypatch, {"GetIdletime": ""}, returncode=1)
    with pytest.raises(desktop_usage_info.ToolError, match="nope"):
        idle.getIdleSec()
