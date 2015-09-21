#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import zmq
import logging


def print_info():
    logging.info("zeromq version: %s" % zmq.zmq_version())
    logging.info("pyzmq version:  %s" % zmq.pyzmq_version())


class request_malformed(Exception):
    pass


class track_server:

    def __init__(self):
        self._running = False

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

        while self._running:
            logging.info('listening..')
            try:
                request = rep_socket.recv_json()
            except KeyboardInterrupt:
                logging.info("got keyboard interrupt - exit")
                break
            logging.debug(request)
            try:
                reply = self.handle_request(request)
            except request_malformed as ex:
                reply = {'type': 'error', 'error_type':'request_malformed',
                         'what': str(ex)}
            except Exception as ex:
                reply = {'type': 'error', 'what': str(ex)}

            rep_socket.send_json(reply)

        logging.info('close..')
        rep_socket.close()


def main():
    track_server().run()

if __name__ == '__main__':
    main()
    logging.info('quit')
