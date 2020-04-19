#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Implements the track server which lurks in the background and collect
application data
"""

import argparse
import signal
import time
import sys
import threading
from contextlib import suppress
import traceback
from typing import Dict, Any

import zmq  # type: ignore

import track_base
from track_base.util import log
import desktop_usage_info


class TrackServer:
    """ track activities, provide them to a time_tracker instance and
        run a zmq/json based server which provides the info to external
        consumers like a UI or a web service"""
    def __init__(self) -> None:
        self._running = False
        self._system_monitoring_thread = threading.Thread(
            target=self._system_monitoring_fn,
            daemon=True)
        self._tracker = track_base.TimeTracker()
        self._last_save_time = 0.

    def _save_data(self, interval: int = 20, force: bool = False) -> None:
        if time.time() - self._last_save_time > interval or force:
            log().info('save data..')
            self._tracker.persist()
            self._last_save_time = time.time()

    def _system_monitoring_fn(self) -> None:
        while self._running:
            time.sleep(1)
            self._save_data(interval=120)
            try:
                self._tracker.update()
            except desktop_usage_info.WindowInformationError:
                pass
            except Exception as ex:
                traceback.print_exc()
                log().error("Unhandled Exception: %s", ex)
                raise

            log().debug(self._tracker.get_current_data())

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Doc"""
        def wrong_command_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            raise track_base.errors.RequestMalformed("Command %r not known" % request["cmd"])

        def no_command_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            raise track_base.errors.RequestMalformed('no "cmd" given')

        def quit_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            self._running = False
            self._system_monitoring_thread.join()
            return {'type': 'ok'}

        def version_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"version": str(track_base.version_info)}}

        def apps_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"apps": self._tracker.get_applications_model().__data__()}}

        def current_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"current": self._tracker.get_current_data()}}

        def rules_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"rules": self._tracker.rules()}}

        def set_rules_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            if not "data" in request or not "rules" in request["data"]:
                raise track_base.errors.RequestMalformed('No "rules" provided')
            self._tracker.set_rules(request["data"]["rules"])
            return {'type': 'ok'}

        def note_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"note": self._tracker.note}}

        def set_note_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            if not "data" in request or not "note" in request["data"]:
                raise track_base.errors.RequestMalformed('No "note" provided')
            self._tracker.set_note(request["data"]["note"])
            return {'type': 'ok'}

        def clip_from_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            if not "data" in request or not "index" in request["data"]:
                raise track_base.errors.RequestMalformed('No "index" provided')
            self._tracker.get_applications_model().clip_from(request["data"]["index"])
            # self._save_data(force=True)
            return {'type': 'ok'}

        def clip_to_fn(request: Dict[str, Any]) -> Dict[str, Any]:
            if not "data" in request or not "index" in request["data"]:
                raise track_base.errors.RequestMalformed('No "index" provided')
            self._tracker.get_applications_model().clip_to(request["data"]["index"])
            # self._save_data(force=True)
            return {'type': 'ok'}

        def save_fn(_request: Dict[str, Any]) -> Dict[str, Any]:
            self._save_data(force=True)
            return {'type': 'ok'}

        return {
            None: no_command_fn,
            "quit": quit_fn,
            "version": version_fn,
            "apps": apps_fn,
            "current": current_fn,
            "rules": rules_fn,
            "set_rules": set_rules_fn,
            "note": note_fn,
            "set_note": set_note_fn,
            "clip_from": clip_from_fn,
            "clip_to": clip_to_fn,
            "save": save_fn,
            }.get(request.get("cmd", None), wrong_command_fn)(request)

    def run(self) -> None:
        """Doc"""
        context = zmq.Context()
        # wing disable: undefined-attribute
        rep_socket = context.socket(zmq.REP)
        try:
            rep_socket.bind('tcp://127.0.0.1:3456')
        except zmq.ZMQError as exc:
            log().error(exc)
            return
        self._running = True

        self._system_monitoring_thread.start()

        while self._running:
            log().debug('listening..')
            try:
                request = rep_socket.recv_json()
            except zmq.ZMQError:
                self._running = False
                self._system_monitoring_thread.join()
                break

            log().debug(request)

            try:
                reply = self.handle_request(request)
            except track_base.errors.RequestMalformed as exc:
                reply = {'type': 'error',
                         'error_type': 'request_malformed',
                         'what': str(exc)}
            except Exception as exc:  # pylint: disable=broad-except
                reply = {'type': 'error', 'what': str(exc)}

            rep_socket.send_json(reply)

        if self._system_monitoring_thread:
            self._system_monitoring_thread.join()

        log().info('close..')
        rep_socket.close()


def parse_arguments() -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    track_base.util.setup_argument_parser(parser)
    return parser.parse_args()


def main() -> None:
    """Doc"""
    args = parse_arguments()
    track_base.util.setup_logging(args, syslog=True)
    track_base.util.log_system_info()

    for sig in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(sig, lambda signal, frame: sys.exit)  # type: ignore
    TrackServer().run()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        main()
