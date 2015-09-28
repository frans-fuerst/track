#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import zmq
import logging
import signal
import time
import sys
import threading

from desktop_usage_info import idle
from desktop_usage_info import applicationinfo

import track_common
import track_base

log = logging.getLogger('track_server')

def print_info():
    log.info("zeromq version: %s" % zmq.zmq_version())
    log.info("pyzmq version:  %s" % zmq.pyzmq_version())
    log.info("track version:  %s" % str(track_base.version_info))


class request_malformed(Exception):
    pass


class track_server:
    ''' track activities, provide them to a time_tracker instance and
        run a zmq/json based server which provides the info to external
        consumers like a UI or a web service
    '''

    def __init__(self):
        self._running = False
        self._system_monitoring_thread = None
        self._tracker = track_base.time_tracker()

    def _system_monitoring_fn(self):
        while self._running:
            time.sleep(1)
            _idle_current = None
            _current_app_title = None
            _current_process_exe = None
            try:
                self._tracker.update()
            except applicationinfo.UncriticalException as e:
                pass

            log.info(self._tracker.get_idle())
            log.info(self._tracker.get_current_app_title())
            log.info(self._tracker.get_current_process_name())

    def handle_request(self, request):
        if 'type' not in request:
            raise request_malformed('no "type" given')

        elif request['type'] == 'quit':
            self._running = False
            return {'type': 'ok'}
        elif request['type'] == 'version':
            return {'version': str(track_base.version_info)}
        elif request['type'] == 'info':
            return {'type': 'info', 'apps': self._tracker.get_applications_model().__data__()}
        elif request['type'] == 'rules':
            return {'type': 'info', 'rules': self._tracker.get_rules_model().__data__()}
        else:
            raise request_malformed(
                'command "%s" not known' % request['type'])

    def run(self):
        print_info()

        context = zmq.Context()
        rep_socket = context.socket(zmq.REP)
        try:
            rep_socket.bind('tcp://127.0.0.1:3456')
        except zmq.ZMQError as e:
            log.error(e)
            return

        self._running = True

        self._system_monitoring_thread = threading.Thread(
            target=self._system_monitoring_fn)
        self._system_monitoring_thread.daemon = True
        self._system_monitoring_thread.start()

        while self._running:
            log.info('listening..')
            try:
                request = rep_socket.recv_json()
            except zmq.ZMQError:
                self._running = False
                self._system_monitoring_thread.join()
                break
            except KeyboardInterrupt:
                log.info("got keyboard interrupt - exit")
                break

            log.debug(request)

            try:
                reply = self.handle_request(request)
            except request_malformed as ex:
                reply = {'type': 'error', 'error_type':'request_malformed',
                         'what': str(ex)}
            except Exception as ex:
                reply = {'type': 'error', 'what': str(ex)}

            rep_socket.send_json(reply)

        if self._system_monitoring_thread:
            self._system_monitoring_thread.join()

        log.info('close..')
        rep_socket.close()


def main():
    track_server().run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(s, lambda signal, frame: sys.exit)

    main()
    log.info('quit')
