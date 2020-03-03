#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
import zmq

def test_track_server():
    p = subprocess.Popen([sys.executable, './track_server.py'])
    
    context = zmq.Context()
    req_socket = context.socket(zmq.REQ)
    req_socket.connect('tcp://127.0.0.1:3456')
    time.sleep(2)
    req_socket.send_json({'type': 'quit'})
    req_socket.recv_json()
    
    print('wait for server to terminate')
    p.wait()
    print('server terminated')

if __name__ == '__main__':
    test_track_server()
