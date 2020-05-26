#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Track main UI module
"""

import sys
import argparse
import os.path
import subprocess
from contextlib import suppress
from typing import Any

try:
    from PyQt5 import QtWidgets, QtGui, QtCore  # type: ignore
except ImportError:
    print("you have to have PyQt5 for your version of Python (%s) installed"
          % ".".join(str(x) for x in sys.version_info))
    sys.exit(-1)

#from .. import core
from ..core import common, errors, util
from ..core.util import log

from .mainwindow import MainWindow
from .qreordertableview import ReorderTableView
from .time_tracker_qt import TimeTrackerClientQt
from .timegraph import EvaluationWidget, FileDataprovider
from .qt_common import CategoryColor, SimpleQtThread


def start_server_process(args) -> None:
    """Start the track server"""
    log().info('start track server daemon')
    server_file = os.path.join(os.path.dirname(__file__), '../../track-server')
    subprocess.Popen([
        sys.executable, server_file,
        "--log-level", args.log_level,
        "--data-dir", args.data_dir,
        "--port", str(args.port),
    ])


def category_name(value):
    """Maps category value to names"""
    return {
        0: "idle",
        1: "unassigned",
        2: "work",
        3: "private",
        4: "break",
        }.get(value, "?")


def check_for_updates() -> None:
    """Identifies whether the track instance is git versioned, fetches from upstream and
    checks whether there are updates to pull"""
    log().info("Check for remote app updates on git remote..")
    def git_cmd(cmd) -> str:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            universal_newlines=True)
        for line in (l for l in result.stderr.split("\n") if l.strip() != ""):
            log().debug("git: %r", line)
        return result.stdout.rstrip("\n")

    try:
        origin = git_cmd(["config", "--get", "remote.origin.url"])
        log().debug("Git repo origin: %r", origin)
        if "frans-fuerst/track" not in origin:
            log().info("Identified git repo is not the original one - skip fetch")
            return
        for line in git_cmd(["fetch"]):
            log().debug(line)
        local_sha = git_cmd(["rev-parse", "@"])
        remote_sha = git_cmd(["rev-parse", "@{u}"])
        base_sha = git_cmd(["merge-base", "@", "@{u}"])
        return (0 if local_sha == remote_sha else
                1 if remote_sha == base_sha else
                2 if local_sha == base_sha else
                3)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log().warning("Was not able to check for git updates: %r", exc)


class TrackUI(MainWindow):
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
                option.backgroundBrush = QtGui.QBrush(CategoryColor(index.data()))

        def displayText(self, value: Any, locale: QtCore.QLocale) -> Any:
            """Convert from category to category names"""
            return (category_name(value) if isinstance(value, int) else
                    super().displayText(value, locale))

    class RulesTableDelegate(QtWidgets.QStyledItemDelegate):
        """Delegator which draws a coloured background for a certain column"""
        def initStyleOption(
                self,
                option: QtWidgets.QStyleOptionViewItem,
                index: QtCore.QModelIndex) -> None:
            """Set text style and color"""
            super().initStyleOption(option, index)
            if index.column() == 0:
                option.font.setFamily("Courier New")
                if index.data() == "":
                    option.displayAlignment = QtCore.Qt.AlignCenter
            if index.column() == 1:
                option.displayAlignment = QtCore.Qt.AlignCenter
                option.backgroundBrush = QtGui.QBrush(CategoryColor(index.data()))

        def displayText(self, value: Any, locale: QtCore.QLocale) -> Any:
            """Convert from category to category names"""
            return (category_name(value) if isinstance(value, int) else
                    "new rule" if value == "" else
                    super().displayText(value, locale))

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()

        self._args = args

        self.txt_notes = QtWidgets.QTextEdit()

        font = QtGui.QFont("FreeMono")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(12)
        font.setBold(True)
        self.txt_notes.setFont(font)
        self.txt_notes.setPlaceholderText("Write a line about what you're doing today")
        self.txt_notes.setAcceptRichText(False)
        self.txt_notes.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        self.notes_spoiler.setTitle("Daily notes")
        self.notes_spoiler.addWidget(self.txt_notes)
        self.notes_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.notes_spoiler.setExpanded(True)

        self.tbl_category_rules = ReorderTableView()
        self.regex_spoiler.setTitle("Category assignment rules (caution: regex)")
        self.regex_spoiler.addWidget(self.tbl_category_rules)
        self.regex_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.active_applications_spoiler.setTitle("Active Applications")
        self.active_applications_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.tbl_active_applications = QtWidgets.QTableView()
        self.active_applications_spoiler.addWidget(self.tbl_active_applications)
        self.active_applications_spoiler.setExpanded(True)

        self.tbl_evaluation = QtWidgets.QListWidget()
        for filename in sorted(
            (file for file in os.listdir(args.data_dir)
             if not '-log-' in file and "rules" not in file and file.endswith(".json")),
            reverse=True
        ):
            myQCustomQWidget = EvaluationWidget(
                dataprovider=FileDataprovider(os.path.join(args.data_dir, filename)))
            myQListWidgetItem = QtWidgets.QListWidgetItem(self.tbl_evaluation)
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            self.tbl_evaluation.addItem(myQListWidgetItem)
            self.tbl_evaluation.setItemWidget(myQListWidgetItem, myQCustomQWidget)

        self.evaluation_spoiler.setTitle("Evaluation")
        self.evaluation_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.evaluation_spoiler.addWidget(self.tbl_evaluation)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_spoiler.setTitle("Log messages")
        self.log_spoiler.addWidget(self.log_view)
        self.log_spoiler.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.log_spoiler.setExpanded(True)

        self.setup_common_widgets()

        common.log_system_info(args)

        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSeekForward))
        self.setGeometry(0, 0, 700, 800)
        self.tray_icon = self._initialize_tray_icon()

        self._endpoint = "tcp://127.0.0.1:%s" % str(args.port)
        self._tracker = TimeTrackerClientQt(self)

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self.update_idle)

        self._start_git_update_check()

        self.pb_quit_server.setVisible(os.environ.get("USER", "") in {"frafue", "frans"})

        self.frm_timegraph.set_dataprovider(self._tracker)

        self.tbl_active_applications.setModel(self._tracker.get_applications_model())
        self.tbl_active_applications.setSortingEnabled(True)
        self.tbl_active_applications.verticalHeader().setVisible(False)
        active_applications_header = self.tbl_active_applications.horizontalHeader()
        active_applications_header.setSortIndicatorShown(True)
        active_applications_header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        active_applications_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        active_applications_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        active_applications_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.tbl_active_applications.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tbl_active_applications.setDragEnabled(True)
        self.tbl_active_applications.setItemDelegate(self.ApplicationTableDelegate())
        self.tbl_active_applications.selectionModel().currentRowChanged.connect(self.cc)

        self.tbl_category_rules.setModel(self._tracker.get_rules_model())

        category_rules_header = self.tbl_category_rules.horizontalHeader()
        category_rules_header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        category_rules_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        category_rules_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tbl_category_rules.setItemDelegate(self.RulesTableDelegate())

    def cc(self, current):
        if not current.column() == 0:
            return
        self._tracker.get_rules_model().check_string(current.data())

    @QtCore.pyqtSlot()
    def on_txt_notes_textChanged(self):
        self._tracker.set_note(self.txt_notes.toPlainText())

    @QtCore.pyqtSlot()
    def on_pb_quit_server_clicked(self) -> None:
        self._tracker.quit_server()
        self.close()

    def update_idle(self) -> None:
        self._tracker.update()
        self.frm_timegraph.update_widgets()
        self.lbl_title.setMargin(2)
        self.lbl_idle.setMargin(2)
        self.lbl_process.setMargin(4)
        self.lbl_title.setText(self._tracker.get_current_app_title())
        self.lbl_idle.setText("%ds" % self._tracker.get_idle())
        self.lbl_process.setText(self._tracker.get_current_process_name())

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
                start_server_process(self._args)

    @QtCore.pyqtSlot()
    def _show_info_popup(self):
        if QtWidgets.QMessageBox.question(
                self,
                "Good news everyone!",
                "Looks like Track has been updated on GitHub.\n"
                "Maybe you should give it a try and run `git pull` (manually)!\n"
                "Do you want to close Track (and its server)?"
                ) == QtWidgets.QMessageBox.Yes:
            self._tracker.quit_server()
            self.close()

    @QtCore.pyqtSlot()
    def _git_update_timer_timeout(self):
        QtCore.QTimer.singleShot(10 * 60 * 1000, self._start_git_update_check)

    def _start_git_update_check(self):
        def check_and_restart():
            git_state = check_for_updates()
            if git_state == 0:
                log().info("Local track repository is in sync with GitHub")
            elif git_state == 1:
                log().info("You have local commits not pushed yet")
            elif git_state in {2, 3}:
                QtCore.QMetaObject.invokeMethod(
                    self, '_show_info_popup', QtCore.Qt.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(
                self, '_git_update_timer_timeout', QtCore.Qt.QueuedConnection)

        self._just_to_keep_the_thread = SimpleQtThread(target=check_and_restart)

    def keyPressEvent(self, event: QtCore.QEvent) -> bool:
        if event.key() == QtCore.Qt.Key_Delete and self.tbl_category_rules.hasFocus():
            rows = set(index.row() for index in self.tbl_category_rules.selectedIndexes())
            for row in rows:
                self._tracker.get_rules_model().removeRow(row)
            self.tbl_category_rules.update()

        return super().keyPressEvent(event)

    def event(self, event: QtCore.QEvent) -> bool:
        """Handle Qt events"""
        _type = event.type()
        if isinstance(event, QtGui.QShowEvent) and not self._tracker.connected:
            if self._connect():
                self._update_timer.start(1000)
                self.txt_notes.setText(self._tracker.note())
                self.log_spoiler.setExpanded(False)

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

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """Shut down gracefully (i.e. close threads)"""
        log().info(
            "Application is about to close %s",
            "(but server still running)" if self._tracker.connected else "")
        self._update_timer.stop()
        if self._tracker.initialized():
            with suppress(errors.NotConnected, RuntimeError):
                self._tracker.save()
        return super().closeEvent(event)


def parse_arguments() -> argparse.Namespace:
    """parse command line arguments and return argument object"""
    parser = argparse.ArgumentParser(description=__doc__)
    common.setup_argument_parser(parser)
    return parser.parse_args()


def main() -> int:
    """read command line arguments, configure application and run command
    specified on command line
    """
    args = parse_arguments()
    util.setup_logging(args)
    app = QtWidgets.QApplication(sys.argv)

    window = TrackUI(args)
    window.show()

    return app.exec_()
