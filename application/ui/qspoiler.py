#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines QSpoiler"""

from PyQt5 import QtWidgets, QtCore


class QSpoiler(QtWidgets.QFrame):
    """Collapsable spoiler widget
        References:
            # Adapted from c++ version
            http://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
    """
    def __init__(self, parent=None, title: str = "", expanded: bool = False) -> None:
        """Improvise a collapsable QFrame"""
        def set_widget_properties(checked: bool) -> None:
            self._content_area.setVisible(checked)
            self._toggle_button.setArrowType(
                QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)

        super().__init__(parent=parent)
        self._content_area = QtWidgets.QWidget()
        self._header_line = QtWidgets.QFrame()
        self._toggle_button = QtWidgets.QToolButton()
        self._main_layout = QtWidgets.QGridLayout()

        self._toggle_button.setStyleSheet("QToolButton { border: none; }")
        self._toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setTitle(title)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(expanded)

        set_widget_properties(self._toggle_button.isChecked())

        self._header_line.setFrameShape(QtWidgets.QFrame.HLine)
        self._header_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self._header_line.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self._content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self._main_layout.setVerticalSpacing(0)
        self._main_layout.setHorizontalSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._toggle_button, 0, 0, 1, 1, QtCore.Qt.AlignLeft)
        self._main_layout.addWidget(self._header_line, 0, 2, 1, 1)
        self._main_layout.addWidget(self._content_area, 1, 0, 1, 3)

        super().setLayout(self._main_layout)

        default_layout = QtWidgets.QVBoxLayout()
        default_layout.setContentsMargins(10, 0, 0, 0)
        self.setLayout(default_layout)

        self._toggle_button.toggled.connect(set_widget_properties)

    def setExpanded(self, expanded: bool) -> None:
        self._toggle_button.setChecked(expanded)

    def setTitle(self, title: str) -> None:
        """Sets the widget title"""
        self._toggle_button.setText(title)

    def layout(self) -> QtWidgets.QLayout:
        """Returns the layout of the content area"""
        return self._content_area.layout()

    def setLayout(self, content_layout: QtWidgets.QLayout) -> None:
        """Sets the content area layout"""
        self._content_area.destroy()
        self._content_area.setLayout(content_layout)

    def addWidget(self, widget: QtWidgets.QWidget) -> None:
        """Adds a widget to the content areas layout"""
        self.layout().addWidget(widget)
