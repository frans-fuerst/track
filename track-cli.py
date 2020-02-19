#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# pylint: disable=expression-not-assigned

""" track-cli - CLI interface to track

"""

################################################################################

import os
import sys
from contextlib import suppress
import argparse

from typing import Any, Dict, List, Set

from util import setup_logging, log, setup_argument_parser, show_system_info


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    setup_argument_parser(parser)

    subparsers = parser.add_subparsers(help='available commands', metavar="CMD")

    parser_help = subparsers.add_parser('help', help='show this help')
    parser_help.set_defaults(func=lambda *_: parser.print_help())

    parser_populate = subparsers.add_parser(
        'populate', help='traverse an SNMP walk and provide needed MIB files')
    parser_populate.set_defaults(func=fn_populate)
    parser_populate.add_argument("snmp_thing",
                                 nargs="+",
                                 metavar="SNMP-WALK-FILE",
                                 help="One or more SNMP OIDs or walk files to process")

    parser.set_defaults(func=lambda *a: parser.print_usage())

    return parser.parse_args(argv)


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


def main(argv=None) -> int:
    """read command line arguments, configure application and run command
    specified on command line"""
    args = parse_arguments(argv or sys.argv[1:])
    setup_logging(args)

    show_system_info()

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

    elif args == ['save']:
        request = {'type': 'save'}

    elif args == ['help']:
        print(['quit', 'version', 'apps', 'current', 'rules'])
        sys.exit()

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


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())

