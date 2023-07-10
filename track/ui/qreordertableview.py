#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Defines QSpoiler"""

from PyQt5 import QtWidgets, QtCore, QtGui


class ReorderTableView(QtWidgets.QTableView):
    """QTableView with the ability to make the model move a row with drag & drop"""

    class DropmarkerStyle(QtWidgets.QProxyStyle):
        """Makes a QTableView behave"""
        def drawPrimitive(
                self,
                element: QtWidgets.QStyle.PrimitiveElement,
                option: QtWidgets.QStyleOption,
                painter: QtGui.QPainter,
                widget: QtWidgets.QWidget = None) -> None:
            """Draw a line across the entire row rather than just the column we're hovering over.
            This may not always work depending on global style - for instance I think it won't
            work on OSX."""
            if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
                option_new = QtWidgets.QStyleOption(option)
                option_new.rect.setLeft(0)
                if widget:
                    option_new.rect.setRight(widget.width())
                option = option_new
            super().drawPrimitive(element, option, painter, widget)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.verticalHeader().hide()
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)
        self.setStyle(self.DropmarkerStyle())

        #self.tbl_category_rules.setDragEnabled(True)
        #self.tbl_category_rules.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        #self.tbl_category_rules.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        #self.tbl_category_rules.setAcceptDrops(True)
        #self.tbl_category_rules.setDropIndicatorShown(True)

        #self.tbl_category_rules.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        #self.tbl_category_rules.viewport().setAcceptDrops(True)
        #self.tbl_category_rules.setDragDropOverwriteMode(False)


    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Identifies source/target row of a finished drag&drop and runs moveRow() on the model"""
        if (event.source() is not self or
                (event.dropAction() != QtCore.Qt.MoveAction and
                 self.dragDropMode() != QtWidgets.QAbstractItemView.InternalMove)):
            super().dropEvent(event)

        selection = self.selectedIndexes()
        from_index = selection[0].row() if selection else -1
        to_index = self.indexAt(event.pos()).row()
        if (0 <= from_index < self.model().rowCount() and
                0 <= to_index < self.model().rowCount() and
                from_index != to_index):
            self.model().moveRow(QtCore.QModelIndex(), from_index, QtCore.QModelIndex(), to_index)
            event.accept()
        super().dropEvent(event)
