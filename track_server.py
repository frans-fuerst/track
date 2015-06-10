#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import zmq
import logging

def print_info():
    logging.info("zeromq version: %s" % zmq.zmq_version())
    logging.info("pyzmq version: %s" % zmq.pyzmq_version())
    
    
def main():
    print_info()

    context = zmq.Context()
    rep_socket = context.socket(zmq.REP)
    rep_socket.bind('tcp://127.0.0.1:3456')

    while True:
        print('listening..')
        try:
            request = rep_socket.recv_json()
        except KeyboardInterrupt:
            print("got keyboard interrupt - exit")
            break
        print(request)
        reply = {'type': 'error'}
        try:
            if 'type' not in request:
                reply = {'type': 'error'}
            elif request['type'] == 'quit':
                reply = {'type': 'ok'}
            else:
                reply = {
                    'type': 'error', 
                    'what': 'command "%s" '
                    'not known' % request['type']}
        except Exception as e:
            reply = {'type': 'error', 'what': str(e)}

        rep_socket.send_json(reply)
        if 'type' in request and request['type'] == 'quit':
            print('quit!')
            break
    print('close..')
    rep_socket.close()

if __name__ == '__main__':
    main()
    print('quit')
    