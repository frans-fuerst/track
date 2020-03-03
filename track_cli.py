#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# pylint: disable=expression-not-assigned

""" track-cli - CLI interface to track

"""

import os
import sys
from contextlib import suppress
import argparse
import json

from typing import List

from track_base.active_applications import active_applications
from util import setup_logging, log, setup_argument_parser, show_system_info


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    setup_argument_parser(parser)

    subparsers = parser.add_subparsers(help='available commands', metavar="CMD")

    parser_help = subparsers.add_parser('help', help='show this help')
    parser_help.set_defaults(func=lambda *_: parser.print_help())

    parser_list = subparsers.add_parser('list', help='list basic logs')
    parser_list.set_defaults(func=fn_info)
    parser_list.add_argument("element", nargs="*")

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


def fn_info(args) -> None:
    def to_time(value):
        return "%2d:%.2d" % (value // 60, value % 60)
    log_dir = os.path.expanduser("~/.track")
    if args.element:
        log().info("Show infos for %r", args.element)
        for file in args.element:
            apps = active_applications(json.load(open(os.path.join(log_dir, file))))
            print("%s: %s - %s = %s => %s" % (
                file,
                  to_time(apps.begin_index()),
                  to_time(apps.end_index()),
                  to_time(apps.end_index() - apps.begin_index()),
                  to_time(apps.end_index() - apps.begin_index() - 60)))
            for time in (t for t in range(apps.begin_index(), apps.end_index()) if t in apps._minutes):
                print(to_time(time))

    else:
        log().info("List recorded data")
        for file in (
            f
            for f in sorted(os.listdir(log_dir)) if not '-log-' in f and f.endswith(".json")
        ):
            apps = active_applications(json.load(open(os.path.join(log_dir, file))))
            print("%s: %s - %s = %s => %s" % (
                file,
                  to_time(apps.begin_index()),
                  to_time(apps.end_index()),
                  to_time(apps.end_index() - apps.begin_index()),
                  to_time(apps.end_index() - apps.begin_index() - 60)))
            #print("".join(("X" if minute in apps._minutes else " ")
            #        for minute in range(apps.begin_index(), apps.end_index() + 1)))


def main(argv=None) -> int:
    """read command line arguments, configure application and run command
    specified on command line"""
    args = parse_arguments(argv or sys.argv[1:])
    setup_logging(args)

    show_system_info()

    args.func(args)

    '''
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
    '''

if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())

