#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import zmq
import logging

log = logging.getLogger('track_cli')

def print_info():
    log.info("zeromq version: %s" % zmq.zmq_version())
    log.info("pyzmq version:  %s" % zmq.pyzmq_version())

def send_request(request):
    context = zmq.Context()
    req_socket = context.socket(zmq.REQ)

    req_socket.connect('tcp://127.0.0.1:3456')

    req_socket.send_json(request)
    return req_socket.recv_json()

def handle_result(result):
    if 'type' in result and result['type'] == 'error':
        raise Exception('server replied with error: "%s"' % result['what'])
    print(result)
    
def main():
    args = sys.argv[1:]

    if args == []:
        print('no command provided')
        return
    elif args == ['quit']:
        request = {'type': 'quit'}
        
    elif args == ['version']:
        request = {'type': 'version'}

    elif args == ['apps']:
        request = {'type': 'apps'}
        
    elif args == ['current']:
        request = {'type': 'current'}
        
    elif args == ['rules']:
        request = {'type': 'rules'}
        
    else:
        raise Exception('command not handled: %s' % args)
    
    try:
        result = send_request(request)
        handle_result(result)
    except zmq.ZMQError as e:
        log.error(e)
        return
    except KeyboardInterrupt:
        log.info("got keyboard interrupt - exit")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
