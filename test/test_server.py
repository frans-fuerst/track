#!/usr/bin/env python3
"""System test: starts a real server process and talks to it over zmq"""

import socket
import subprocess
import sys

import pytest
import zmq

pytestmark = pytest.mark.system


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(port: int, cmd: str):
    req_socket = zmq.Context.instance().socket(zmq.REQ)
    req_socket.setsockopt(zmq.LINGER, 0)
    req_socket.connect("tcp://127.0.0.1:%d" % port)
    req_socket.send_json({"cmd": cmd})
    assert req_socket.poll(5000), "server did not answer"
    return req_socket.recv_json()


def test_track_server(tmp_path):
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "track.cli", "--data-dir", str(tmp_path), "--port", str(port), "serve"]
    )
    try:
        assert "version" in request(port, "version")["data"]
        assert request(port, "quit") == {"type": "ok"}
        assert server.wait(timeout=10) == 0
    finally:
        server.kill()
    assert (tmp_path / "category_rules.json").exists()
