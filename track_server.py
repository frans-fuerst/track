#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import zmq
import logging

def print_info():
    logging.info("zeromq version: %s" % zmq.__version__)
    logging.info("zeromq version: %s" % zmq._zmq_version_info)
#    logging.info("zeromq version: %s" % zmq._zmq_version )
    
def main():
    print_info()

if __name__ == '__main__':
    main()