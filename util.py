import os
import sys
import logging
import argparse
import zmq
from typing import Any #, Dict, List, Set


def setup_logging(args):
    use_col = "TERM" in os.environ
    logging.basicConfig(
        format="%(levelname)s %(asctime)s %(name)s: %(message)s" + (
            "\033[0m" if use_col else ""),
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.WARN,
    )
    for l in (
        ("DEBUG", "\033[32m"),
        ("INFO", "\033[36m"),
        ("WARNING", "\033[33m"),
        ("ERROR", "\033[31m"),
        ("CRITICAL", "\033[37m"),
    ):
        logging.addLevelName(
            getattr(logging, l[0]),
            "%s(%s)" % (l[1] if use_col else "", l[0][0] * 2),
        )

    log().setLevel(getattr(logging, args.log_level))


def setup_argument_parser(parser):
    parser.add_argument('--log-level',
                        '-l',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
                        default='INFO',)
    parser.add_argument('--data-dir',
                        '-d',
                        default=os.path.expanduser('~/.track'),)


def catch(func, exceptions, default=None) -> Any:
    """de-uglyfy assignments with potential known exceptions"""
    try:
        return func()
    except exceptions:
        return default


def log(name="track") -> logging.Logger:
    """Convenience function to access logger 'app logger'"""
    return logging.getLogger(name)


def show_system_info():
    log().info("Python version: %s (%s)", '.'.join((str(e) for e in sys.version_info)), sys.executable)
    log().info("zeromq version: %s" % zmq.zmq_version())
    log().info("pyzmq version:  %s" % zmq.pyzmq_version())

