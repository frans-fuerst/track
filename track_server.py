#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import zmq
import logging
import time
import threading

from desktop_usage_info import idle
from desktop_usage_info import applicationinfo

log = logging.getLogger('track_server')

def print_info():
    log.info("zeromq version: %s" % zmq.zmq_version())
    log.info("pyzmq version:  %s" % zmq.pyzmq_version())


class request_malformed(Exception):
    pass


class track_server:

    def __init__(self):
        self._running = False
        self._system_monitoring_thread = None
        
    def _system_monitoring_fn(self):
        while self._running:
            time.sleep(1)
            try:
                self._idle_current = idle.getIdleSec()
                self._current_app_title = applicationinfo.get_active_window_title()
                self._current_process_exe = applicationinfo.get_active_process_name()
                log.info('sample')
                print(self._idle_current)
                print(self._current_app_title)
            except applicationinfo.UncriticalException as e:
                pass

    def handle_request(self, request):
        if 'type' not in request:
            raise request_malformed('no "type" given')

        elif request['type'] == 'quit':
            self._running = False
            reply = {'type': 'ok'}

        else:
            raise request_malformed(
                'command "%s" not known' % request['type'])

    def run(self):
        print_info()

        context = zmq.Context()
        rep_socket = context.socket(zmq.REP)
        rep_socket.bind('tcp://127.0.0.1:3456')

        self._running = True

        self._system_monitoring_thread = threading.Thread(
            target=self._system_monitoring_fn)
        self._system_monitoring_thread.start()
        
        while self._running:
            log.info('listening..')
            try:
                request = rep_socket.recv_json()
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
    main()
    log.info('quit')
