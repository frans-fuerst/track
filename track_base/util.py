#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Provide some non-track-specific helper functions"""

import os
import sys
import logging
import logging.handlers
import argparse
from typing import Any

import zmq

import track_base

def setup_logging(args: argparse.Namespace, syslog=False) -> None:
    """Setup coloring, syslog etc"""
    use_col = "TERM" in os.environ
    logging.basicConfig(
        format="%(levelname)s %(asctime)s %(name)s: %(message)s" + (
            "\033[0m" if use_col else ""),
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.WARN,
    )
    for level_name in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        logging.addLevelName(getattr(logging, level_name), level_name[0] * 2)

    log().setLevel(getattr(logging, args.log_level))
    if syslog and os.name == 'posix':
        handler = logging.handlers.SysLogHandler(address='/dev/log')
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s %(name)15s %(levelname)s:  %(message)s",
            datefmt="%y%m%d-%H%M%S"))
        logging.getLogger().addHandler(handler)


def setup_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Set some default arguments for track components"""
    parser.add_argument('--log-level',
                        '-l',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
                        default='INFO',)
    parser.add_argument('--data-dir',
                        '-d',
                        default=os.path.expanduser('~/.track'),)


def throw(exc: Exception) -> None:
    """Use an exception as function"""
    raise exc


def catch(func, exceptions, default=None) -> Any:
    """de-uglyfy assignments with potential known exceptions"""
    try:
        return func()
    except exceptions:
        return default


def log(name="track") -> logging.Logger:
    """Convenience function to access logger 'app logger'"""
    return logging.getLogger(name)


def log_system_info() -> None:
    """Print some interestion system information used for problem solving"""
    log().info("Python version: %s (%r)",
               '.'.join((str(e) for e in sys.version_info)),
               sys.executable)
    log().info("zeromq version: %s", zmq.zmq_version())
    log().info("pyzmq version:  %s", zmq.pyzmq_version())
    log().info("track version:  %s", str(track_base.version_info))
