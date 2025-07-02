from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QFrame
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSlot
from PyQt5.QtGui import QColor, QPainter, QTextFormat
import os

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
        self.dark_mode = False

    def set_dark_mode(self, dark):
        self.dark_mode = dark
        self.update()

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event, self.dark_mode)

class SQLPlainTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark_mode = False
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def set_dark_mode(self, dark):
        self._dark_mode = dark
        pal = self.palette()
        if dark:
            pal.setColor(self.backgroundRole(), QColor('#232629'))
            pal.setColor(self.foregroundRole(), QColor('#F0F0F0'))
            self.setStyleSheet('background:#232629; color:#F0F0F0; selection-background-color:#44475a; selection-color:#ffffff;')
        else:
            self.setStyleSheet('')
        self.line_number_area.set_dark_mode(dark)
        self.update()
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().width('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event, dark_mode=False):
        painter = QPainter(self.line_number_area)
        if dark_mode:
            painter.fillRect(event.rect(), QColor('#232629'))
            pen_color = QColor('#888')
        else:
            painter.fillRect(event.rect(), QColor(240, 240, 240))
            pen_color = Qt.gray
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(pen_color)
                painter.drawText(0, top, self.line_number_area.width() - 2, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor('#333950') if self._dark_mode else QColor(235, 235, 255)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

class SQLEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.sql_edit = SQLPlainTextEdit()
        self.sql_edit.setPlaceholderText('请输入SQL语句...')
        layout.addWidget(self.sql_edit)

        btn_layout = QHBoxLayout()
        self.exec_btn = QPushButton('执行')
        btn_layout.addWidget(self.exec_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.result_label = QLabel('')
        layout.addWidget(self.result_label)
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

    def set_result(self, headers, rows):
        self.result_table.clear()
        if not headers:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        if not rows:
            self.result_table.setRowCount(0)
            return
        self.result_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                self.result_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
