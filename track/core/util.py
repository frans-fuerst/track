#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Provide some non-track-specific helper functions"""

import argparse
import logging
import logging.handlers
import os
from typing import Any


class ColorFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    colors = {
        "green": "\x1b[32m",
        "cyan": "\x1b[36m",
        "grey": "\x1b[38;21m",
        "yellow": "\x1b[33;21m",
        "red": "\x1b[31;21m",
        "bold_red": "\x1b[31;1m",
        "reset": "\x1b[0m",
    }
    level_colors = {
        logging.DEBUG: colors["green"],
        logging.INFO: colors["cyan"],
        logging.WARNING: colors["yellow"],
        logging.ERROR: colors["red"],
        logging.CRITICAL: colors["bold_red"],
    }
    use_color = "TERM" in os.environ

    def format(self, record):
        return (
            self.level_colors[record.levelno] + super().format(record) + self.colors["reset"]
            if self.use_color
            else super().format(record)
        )


def setup_logging(args: argparse.Namespace, syslog=False) -> None:
    """Setup coloring, syslog etc"""
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColorFormatter(
            fmt="%(levelname)s %(asctime)s %(name)s %(process)s:%(thread)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.getLogger().addHandler(handler)
    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        logging.addLevelName(getattr(logging, level), "(%s)" % (level[0] * 2))

    log().setLevel(getattr(logging, args.log_level))
    if syslog and os.name == "posix":
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(name)15s %(levelname)s:  %(message)s", datefmt="%y%m%d-%H%M%S"
            )
        )
        logging.getLogger().addHandler(handler)


def catch(func, exceptions, default=None) -> Any:
    """de-uglyfy assignments with potential known exceptions"""
    try:
        return func()
    except exceptions:
        return default


def log(name: str = "main") -> logging.Logger:
    """Convenience function to access logger 'app logger'"""
    return logging.getLogger(name)


def exception_to_string(exc: Exception) -> str:
    """Turn an exception into something very readable
    Currently only __str__ is being used - to be enrichted by file, etc"""
    return "%r" % exc
