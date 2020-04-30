#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Track main UI module
"""

import sys
import signal
import argparse
import os.path
import json
import subprocess
from contextlib import suppress
from typing import Any

try:
    from PyQt5 import QtWidgets, QtGui, QtCore, uic  # type: ignore
except ImportError:
    print("you have to have PyQt5 for your version of Python (%s) installed"
          % ".".join(str(x) for x in sys.version_info))
    sys.exit(-1)

import track_base
from track_base import mins_to_dur
from track_base.util import log
import track_qt
from track_qt import CategoryColor


def start_server_process() -> None:
    """Start the track server"""
    log().info('start track server daemon')
    server_file = os.path.join(os.path.dirname(__file__), 'track-server')
    subprocess.Popen([sys.executable, server_file])


class TrackUI(QtWidgets.QMainWindow):
    """Track recorder UI"""
    class ApplicationTableDelegate(QtWidgets.QStyledItemDelegate):
        """Delegator which draws a coloured background for a certain column"""
        def initStyleOption(
                self,
                option: QtWidgets.QStyleOptionViewItem,
                index: QtCore.QModelIndex) -> None:
            """Set text style and color"""
            super().initStyleOption(option, index)
            if index.column() == 2:
                # option.font.setBold(True)
                option.backgroundBrush = QtGui.QBrush(CategoryColor(index.data()))

        def displayText(self, value: Any, locale: QtCore.QLocale) -> Any:
            """Convert from category to category names"""
            return (
                {
                    0: "idle",
                    1: "unassigned",
                    2: "work",
                    3: "private",
                    4: "break",
                }.get(value, "?") if isinstance(value, int) else
                super().displayText(value, locale))

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()
        self.windowTitleChanged.connect(self.on_windowTitleChanged)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'track.ui'), self)

        self.tbl_category_rules = QtWidgets.QTableView()
        self.regex_spoiler.setTitle("Category assignment rules (caution: regex)")
        self.regex_spoiler.addWidget(self.tbl_category_rules)
        self.regex_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.tbl_evaluation = QtWidgets.QTextEdit()
        self.tbl_evaluation.setReadOnly(True)
        self.tbl_evaluation.setLineWrapMode(0)
        self.tbl_evaluation.setFontFamily("Courier New")
        self.tbl_evaluation.setPlainText(self._render_evaluation_text(args.data_dir))
        self.evaluation_spoiler.setTitle("Evaluation")
        self.evaluation_spoiler.addWidget(self.tbl_evaluation)
        self.evaluation_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setLineWrapMode(0)
        self.txt_log.setFontFamily("Courier New")
        self.txt_log.setPlainText("nothing to see here")
        self.log_spoiler.setTitle("Log messages")
        self.log_spoiler.addWidget(self.txt_log)
        self.log_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSeekForward))
        self.setGeometry(0, 0, 700, 800)
        self.tray_icon = self._initialize_tray_icon()

        self._endpoint = "tcp://127.0.0.1:%s" % str(args.port)
        self._tracker = track_qt.TimeTrackerClientQt(self)

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self.update_idle)

        self.pb_quit_server.setVisible(os.environ["USER"] in {"frafue", "frans"})

        self.frm_timegraph.setTracker(self._tracker)

        self.tbl_active_applications.setModel(self._tracker.get_applications_model())
        active_applications_header = self.tbl_active_applications.horizontalHeader()
        active_applications_header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        active_applications_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        active_applications_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        active_applications_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.tbl_active_applications.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tbl_active_applications.setDragEnabled(True)
        self.tbl_active_applications.setDropIndicatorShown(True)
        self.tbl_active_applications.setItemDelegate(self.ApplicationTableDelegate())
        self.tbl_active_applications.selectionModel().currentRowChanged.connect(self.cc)

        self.tbl_category_rules.setModel(self._tracker.get_rules_model())

        self.tbl_category_rules.setDragEnabled(True)
        self.tbl_category_rules.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_category_rules.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.tbl_category_rules.setDragEnabled(True)
        self.tbl_category_rules.setAcceptDrops(True)
        self.tbl_category_rules.setDropIndicatorShown(True)

        self.tbl_category_rules.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tbl_category_rules.viewport().setAcceptDrops(True)
        self.tbl_category_rules.setDragDropOverwriteMode(False)

        category_rules_header = self.tbl_category_rules.horizontalHeader()
        category_rules_header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        category_rules_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        category_rules_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        self.tbl_category_rules.verticalHeader().setSectionsMovable(True)
        self.tbl_category_rules.verticalHeader().setDragEnabled(True)
        self.tbl_category_rules.verticalHeader().setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

    def cc(self, current):
        if not current.column() == 0:
            return
        self._tracker.get_rules_model().check_string(current.data())

    def _initialize_tray_icon(self) -> QtWidgets.QSystemTrayIcon:
        def restore_window(reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
            if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
                self.tray_icon.hide()
                self.showNormal()

        tray_icon = QtWidgets.QSystemTrayIcon(self)
        tray_icon.setIcon(self.windowIcon())
        tray_icon.activated.connect(restore_window)
        return tray_icon

    def on_windowTitleChanged(self, title: str) -> None:
        QtCore.QCoreApplication.setApplicationName(title)
        self.setWindowIconText(title)

    def on_txt_notes_textChanged(self):
        self._tracker.set_note(self.txt_notes.toPlainText())

    def on_pb_quit_server_clicked(self) -> None:
        self._tracker.quit_server()
        self.close()

    def on_frm_timegraph_clipFromClicked(self, index: int) -> None:
        self._tracker.clip_from(index)

    def on_frm_timegraph_clipToClicked(self, index: int) -> None:
        self._tracker.clip_to(index)

    def update_idle(self) -> None:
        self._tracker.update()
        _idle = self._tracker.get_idle()
        self.lbl_title.setMargin(2)
        self.lbl_idle.setMargin(2)
        self.lbl_title.setText(self._tracker.get_current_app_title())
        self.lbl_idle.setText("%ds" % _idle)
        self.lbl_process.setText(self._tracker.get_current_process_name())

        _time_total = self._tracker.get_time_total()
        _time_active = self._tracker.get_time_active()
        _time_work = self._tracker.get_time_work()
        _time_private = self._tracker.get_time_private()
        _time_idle = self._tracker.get_time_idle()
        percentage = 100. / _time_total
        self.lbl_time_active.setText("active: %s (%d%%)" % (
            mins_to_dur(_time_active), _time_active * percentage))
        self.lbl_time_work.setText("work: %s (%d%%)" % (
            mins_to_dur(_time_work), _time_work * percentage))
        self.lbl_time_private.setText("private: %s (%d%%)" % (
            mins_to_dur(_time_private), _time_private * percentage))
        self.lbl_time_idle.setText("idle: %s (%d%%)" % (
            mins_to_dur(_time_idle), _time_idle * percentage))

        self.lbl_start_time.setText("%s - %s: %s" % (
            self._tracker.start_time(),
            self._tracker.now(),
            mins_to_dur(self._tracker.get_time_total())))

        palette = self.lbl_title.palette()
        palette.setColor(
            self.lbl_title.backgroundRole(),
            CategoryColor(self._tracker.get_current_category())
            if self._tracker.user_is_active() else QtCore.Qt.gray)
        self.lbl_idle.setPalette(palette)
        self.lbl_title.setPalette(palette)

        self.update()

    def _connect(self) -> bool:
        _retried = False
        while True:
            try:
                log().info('connect to track server..')
                self._tracker.connect(self._endpoint)
                log().info('connected!')
                return True
            except TimeoutError:
                if _retried:
                    log().error("could not connect to track server")
                    return False
                log().info(
                    "could not connect to server - assume "
                    "it's not running and start a server instance")
                _retried = True
                start_server_process()

    def _render_evaluation_text(self, path):
        def to_time(value):
            return "%2d:%.2d" % (value // 60, value % 60)
        def convert(data):
            return data if "tracker_data" in data else {"tracker_data": data}
        def to_string(file):
            data = convert(json.load(open(os.path.join(path, file))))
            apps = track_base.ActiveApplications(data["tracker_data"])
            daily_note = data.get("daily_note") or ""
            return("%s: %s - %s = %s => %s (note: %r)" % (
                file.replace(".json", "").replace("track-", ""),
                to_time(apps.begin_index()),
                to_time(apps.end_index()),
                to_time(apps.end_index() - apps.begin_index()),
                to_time(apps.end_index() - apps.begin_index() - 60),
                daily_note.split("\n")[0]))

        return ("More coming soon - this is just a small overview \n\n" +
                "\n".join(to_string(filename) for filename in (
                    f
                    for f in sorted(os.listdir(path), reverse=True)
                    if not '-log-' in f and not "rules" in f and f.endswith(".json"))))



    def keyPressEvent(self, event: QtCore.QEvent) -> bool:
        if event.key() == QtCore.Qt.Key_Delete and self.tbl_category_rules.hasFocus():
            indices = self.tbl_category_rules.selectedIndexes()
            for index in indices:
                self._tracker.get_rules_model().removeRow(index.row())
            self.tbl_category_rules.update()

        return super().keyPressEvent(event)

    def event(self, event: QtCore.QEvent) -> bool:
        """Handle Qt events"""
        _type = event.type()
        if _type == QtCore.QEvent.WindowActivate and not self._tracker.connected:
            # we abuse this event as some sort of WindowShow event
            if self._connect():
                self._update_timer.start(1000)
                self.txt_notes.setText(self._tracker.note())

            else:
                QtWidgets.QMessageBox.information(
                    self, "track service unreachable",
                    "Cannot reach the local track service even after starting "
                    "a new instance.\nPlease restart track on command "
                    "line to get some more info and file a bug!\n\nBye!",
                    buttons=QtWidgets.QMessageBox.Ok)
                QtWidgets.QApplication.quit()
        elif _type == QtCore.QEvent.WindowStateChange and self.isMinimized():
            if "gnome" not in os.environ.get("DESKTOP_SESSION", ""):
                # The window is already minimized at this point.  AFAIK,
                # there is no hook stop a minimize event. Instead,
                # removing the Qt.Tool flag should remove the window
                # from the taskbar.
                self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.Tool)
                self.tray_icon.show()
            return True
        else:
            # log.debug("unhandled event '%s' (%d)",
            #         i_to_e[_type] if _type in i_to_e else "unknown",
            #         _type)
            pass

        return super().event(event)  # type: ignore

    def closeEvent(self, _event: QtCore.QEvent) -> None:
        """Shut down gracefully (i.e. close threads)"""
        self._update_timer.stop()
        if self._tracker.initialized():
            with suppress(track_base.not_connected, RuntimeError):
                self._tracker.save()

    def handle_signal(self, sig: int) -> None:
        """Handle posix signals, i.e. shut down on CTRL-C"""
        log().info(
            "got signal %s(%d)",
            dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                 if v.startswith('SIG') and not v.startswith('SIG_')).get(sig, "unknown"),
            sig)
        if sig == signal.SIGINT:
            self.close()


def parse_arguments() -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    track_base.util.setup_argument_parser(parser)
    return parser.parse_args()


def main() -> int:
    """read command line arguments, configure application and run command
    specified on command line
    """
    args = parse_arguments()
    track_base.util.setup_logging(args)
    track_base.util.log_system_info()
    app = QtWidgets.QApplication(sys.argv)
    with suppress(FileNotFoundError):
        with open(os.path.join(os.path.dirname(__file__), "track.qss")) as f:
            app.setStyleSheet(f.read())


    window = TrackUI(args)
    window.show()

    for sig in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(sig, lambda sign, _frame: window.handle_signal(sign))

    # catch the interpreter every now and then to be able to catch
    # signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    return app.exec_()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, BrokenPipeError):
        raise SystemExit(main())
