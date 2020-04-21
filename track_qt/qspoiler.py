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
    def __init__(self, parent=None, title=''):
        """
        """
        def set_widget_properties(checked):
            self._contentArea.setVisible(checked)
            self._toggleButton.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)

        super().__init__(parent=parent)

        self._contentArea = QtWidgets.QWidget()
        self._headerLine = QtWidgets.QFrame()
        self._toggleButton = QtWidgets.QToolButton()

        self._mainLayout = QtWidgets.QGridLayout()

        self._toggleButton.setStyleSheet("QToolButton { border: none; }")
        self._toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setTitle(title)
        self._toggleButton.setCheckable(True)
        self._toggleButton.setChecked(False)

        set_widget_properties(self._toggleButton.isChecked())

        self._headerLine.setFrameShape(QtWidgets.QFrame.HLine)
        self._headerLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self._headerLine.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

        self._contentArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._mainLayout.setVerticalSpacing(0)
        self._mainLayout.setHorizontalSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.addWidget(self._toggleButton, 0, 0, 1, 1, QtCore.Qt.AlignLeft)
        self._mainLayout.addWidget(self._headerLine, 0, 2, 1, 1)
        self._mainLayout.addWidget(self._contentArea, 1, 0, 1, 3)

        super().setLayout(self._mainLayout)

        default_layout = QtWidgets.QVBoxLayout()
        default_layout.setContentsMargins(10, 0, 0, 0)
        self.setLayout(default_layout)

        self._toggleButton.clicked.connect(set_widget_properties)

    def setTitle(self, title):
        """Sets the widget title"""
        self._toggleButton.setText(title)

    def layout(self):
        """Returns the layout of the content area"""
        return self._contentArea.layout()

    def setLayout(self, contentLayout):
        """Sets the content area layout"""
        self._contentArea.destroy()
        self._contentArea.setLayout(contentLayout)

    def addWidget(self, widget):
        """Adds a widget to the content areas layout"""
        self.layout().addWidget(widget)
