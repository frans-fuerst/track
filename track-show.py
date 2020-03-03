#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# pylint: disable=expression-not-assigned

""" track-show - visualize tracked facts

"""

################################################################################

import os
import sys
from contextlib import suppress
import signal
import argparse
from typing import Any, Dict, List, Set
from PyQt5 import QtWidgets, QtGui, QtCore, uic

from util import setup_logging, log, setup_argument_parser, show_system_info


#STYLESHEET = 'QTDark.stylesheet'


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    setup_argument_parser(parser)
    return parser.parse_args(argv)


class TrackShowMainwindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'track-show.ui'), self)
        self._args = args
        self.load_track_files()
        self.resize(800, 500)

    def handle_signal(self, sig: int) -> None:
        log().info("got signal %d" % sig)
        if sig == 2:
            self.close()

    def load_track_files(self):
        for f in os.listdir(self._args.data_dir):
            print(f)


def main(argv=None) -> int:
    """read command line arguments, configure application and run command
    specified on command line"""
    args = parse_arguments(argv or sys.argv[1:])
    setup_logging(args)

    show_system_info()

    app = QtWidgets.QApplication(sys.argv)

    #with open(os.path.join(APP_DIR, STYLESHEET)) as f:
    #    app.setStyleSheet(f.read())

    main_window = TrackShowMainwindow(args)

    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(s, lambda signal, frame: main_window.handle_signal(signal))

    # catch the interpreter every now and then to be able to catch signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)
    main_window.show()
    return app.exec_()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())

