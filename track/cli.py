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

import zmq

from .core import util, common, ActiveApplications
from .core.util import log


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    common.setup_argument_parser(parser)

    subparsers = parser.add_subparsers(help='available commands', metavar="CMD")

    parser_help = subparsers.add_parser('help', help='show this help')
    parser_help.set_defaults(func=lambda *_: parser.print_help())

    parser_list = subparsers.add_parser('list', help='list basic logs')
    parser_list.set_defaults(func=fn_info)

    parser_server = subparsers.add_parser('server', help='send command to server')
    parser_server.set_defaults(func=fn_server)
    parser_server.add_argument("command")

    parser_server = subparsers.add_parser('serve', help='send command to server')
    parser_server.set_defaults(func=fn_serve)

    parser_show = subparsers.add_parser('show', help='show content of one log file')
    parser_show.set_defaults(func=fn_show)
    parser_show.add_argument("element", nargs="+")

    parser_ui = subparsers.add_parser('ui', help='start the track ui')
    parser_ui.set_defaults(func=fn_ui)

    parser.set_defaults(func=fn_ui)

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


def convert(data):
    return data if "tracker_data" in data else {"tracker_data": data}


def to_time(value):
    return "%2d:%.2d" % (value // 60, value % 60)

def fn_ui(args) -> None:
    from track.ui import main as main_ui
    main_ui()

def fn_serve(args) -> None:
    from track.server import main as main_server
    main_server()

def fn_server(args) -> None:
    if args.command not in {"quit", "version", "apps", "current", "rules", "save", "note"}:
        log().error("Command not known: %r", args.command)
        return

    try:
        result = send_request({"cmd": args.command})
        handle_result(result)
    except zmq.ZMQError as e:
        log.error(e)
        return


def fn_show(args) -> None:
    log_dir = args.data_dir

    log().info("Show infos for %r", args.element)
    for file in args.element:
        data = convert(json.load(open(os.path.join(log_dir, file))))
        apps = ActiveApplications(data["tracker_data"])
        daily_note = data.get("daily_note") or ""
        print("%s: %s - %s = %s => %s" % (
            file,
            to_time(apps.begin_index()),
            to_time(apps.end_index()),
            to_time(apps.end_index() - apps.begin_index()),
            to_time(apps.end_index() - apps.begin_index() - 60)))
        for time in (t for t in range(apps.begin_index(), apps.end_index()) if t in apps._minutes):
            print(to_time(time))
        print(daily_note)


def fn_info(args) -> None:
    log_dir = args.data_dir
    log().info("List recorded data")
    for file in common.log_files(log_dir):
        data = convert(json.load(open(os.path.join(log_dir, file))))
        if "20200503" in file:
            print(file)
        apps = ActiveApplications(data["tracker_data"])
        daily_note = data.get("daily_note") or ""
        print("%s: %s - %s = %s => %s (note: %r)" % (
            file,
            to_time(apps.begin_index()),
            to_time(apps.end_index()),
            to_time(apps.end_index() - apps.begin_index()),
            to_time(apps.end_index() - apps.begin_index() - 60),
            daily_note.split("\n")[0]))
        # print("".join(("X" if minute in apps._minutes else " ")
        #        for minute in range(apps.begin_index(), apps.end_index() + 1)))


def main(argv=None) -> int:
    """read command line arguments, configure application and run command
    specified on command line"""

    args = parse_arguments(argv or sys.argv[1:])
    util.setup_logging(args)
    common.log_system_info(args)

    args.func(args)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())
