from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QSpinBox, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from .thread_worker import WorkerThread

class TableDataViewer(QWidget):
    def __init__(self, headers, fetch_page_callback, parent=None, db_client=None, table_name=None, pk_fields=None):
        super().__init__(parent)
        self.headers = headers
        self.fetch_page_callback = fetch_page_callback  # (page, page_size) -> (rows, total)
        self.page = 1
        self.page_size = 20
        self.total = 0
        self.db_client = db_client  # 新增：数据库客户端
        self.table_name = table_name  # 新增：表名
        self.pk_fields = pk_fields or []  # 新增：主键字段名列表
        self._original_data = []  # 原始数据
        self._changes = {}  # {(row, col): new_value}
        self._added_rows = []  # 新增行索引
        self._deleted_rows = set()  # 删除行索引
        self.init_ui()
        self.load_page()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # 编辑按钮区
        editlayout = QHBoxLayout()
        self.add_btn = QPushButton('添加行')
        self.del_btn = QPushButton('删除行')
        self.commit_btn = QPushButton('提交更改')
        self.rollback_btn = QPushButton('撤销更改')
        editlayout.addWidget(self.add_btn)
        editlayout.addWidget(self.del_btn)
        editlayout.addWidget(self.commit_btn)
        editlayout.addWidget(self.rollback_btn)
        editlayout.addStretch()
        layout.addLayout(editlayout)
        # 表格
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)
        layout.addWidget(self.table)
        # 分页控件
        pagelayout = QHBoxLayout()
        self.prev_btn = QPushButton('上一页')
        self.next_btn = QPushButton('下一页')
        self.page_label = QLabel('第 1 页')
        self.page_size_box = QSpinBox()
        self.page_size_box.setRange(1, 1000)
        self.page_size_box.setValue(self.page_size)
        self.goto_edit = QLineEdit()
        self.goto_edit.setPlaceholderText('跳转页')
        self.goto_btn = QPushButton('跳转')
        self.refresh_btn = QPushButton('刷新')
        pagelayout.addWidget(self.prev_btn)
        pagelayout.addWidget(self.next_btn)
        pagelayout.addWidget(self.page_label)
        pagelayout.addWidget(QLabel('每页'))
        pagelayout.addWidget(self.page_size_box)
        pagelayout.addWidget(QLabel('条'))
        pagelayout.addWidget(self.goto_edit)
        pagelayout.addWidget(self.goto_btn)
        pagelayout.addWidget(self.refresh_btn)
        pagelayout.addStretch()
        layout.addLayout(pagelayout)
        # 事件
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.page_size_box.valueChanged.connect(self.change_page_size)
        self.goto_btn.clicked.connect(self.goto_page)
        self.refresh_btn.clicked.connect(self.load_page)
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_selected_rows)
        self.commit_btn.clicked.connect(self.commit_changes)
        self.rollback_btn.clicked.connect(self.rollback_changes)
        self.table.itemChanged.connect(self.on_item_changed)

    def load_page(self):
        self.refresh_btn.setEnabled(False)
        self.table.setDisabled(True)
        def fetch():
            return self.fetch_page_callback(self.page, self.page_size)
        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(self.on_page_loaded)
        self.thread.start()

    def on_page_loaded(self, result, error):
        self.refresh_btn.setEnabled(True)
        self.table.setDisabled(False)
        if error:
            QMessageBox.warning(self, '加载失败', str(error))
            return
        rows, total = result
        self.total = total
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(self.headers)
        self._original_data = [list(row) for row in rows]
        self._changes = {}
        self._added_rows = []
        self._deleted_rows = set()
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)
        self.table.blockSignals(False)
        total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        self.page_label.setText(f'第 {self.page} / {total_pages} 页, 共 {self.total} 条')
        self.prev_btn.setEnabled(self.page > 1)
        self.next_btn.setEnabled(self.page < total_pages)

    def add_row(self):
        self.table.blockSignals(True)
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        for col in range(self.table.columnCount()):
            self.table.setItem(row_idx, col, QTableWidgetItem(''))
        self._added_rows.append(row_idx)
        self.table.blockSignals(False)

    def delete_selected_rows(self):
        selected = self.table.selectionModel().selectedRows()
        for idx in sorted([s.row() for s in selected], reverse=True):
            if idx < len(self._original_data):
                self._deleted_rows.add(idx)
            if idx in self._added_rows:
                self._added_rows.remove(idx)
            self.table.removeRow(idx)

    def on_item_changed(self, item):
        row, col = item.row(), item.column()
        if row < len(self._original_data):
            old = str(self._original_data[row][col]) if self._original_data[row][col] is not None else ''
            if item.text() != old:
                self._changes[(row, col)] = item.text()
            elif (row, col) in self._changes:
                del self._changes[(row, col)]

    def commit_changes(self):
        # 需要db_client, table_name, pk_fields
        if not self.db_client or not self.table_name or not self.pk_fields:
            QMessageBox.warning(self, '提交失败', '缺少数据库信息，无法提交')
            return
        # 新增
        for row_idx in self._added_rows:
            values = [self.table.item(row_idx, col).text() for col in range(self.table.columnCount())]
            try:
                self.db_client.insert_row(self.table_name, self.headers, values)
            except Exception as e:
                QMessageBox.critical(self, '插入失败', f'第{row_idx+1}行: {e}')
                return
        # 修改
        for (row, col), new_value in self._changes.items():
            pk_dict = {pk: self._original_data[row][self.headers.index(pk)] for pk in self.pk_fields}
            try:
                self.db_client.update_row(self.table_name, self.headers[col], new_value, pk_dict)
            except Exception as e:
                QMessageBox.critical(self, '修改失败', f'第{row+1}行: {e}')
                return
        # 删除
        for row_idx in self._deleted_rows:
            pk_dict = {pk: self._original_data[row_idx][self.headers.index(pk)] for pk in self.pk_fields}
            try:
                self.db_client.delete_row(self.table_name, pk_dict)
            except Exception as e:
                QMessageBox.critical(self, '删除失败', f'第{row_idx+1}行: {e}')
                return
        QMessageBox.information(self, '提交成功', '所有更改已提交')
        self.load_page()

    def rollback_changes(self):
        self.load_page()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_page()

    def next_page(self):
        total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        if self.page < total_pages:
            self.page += 1
            self.load_page()

    def change_page_size(self, value):
        self.page_size = value
        self.page = 1
        self.load_page()

    def goto_page(self):
        try:
            p = int(self.goto_edit.text())
            total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
            if 1 <= p <= total_pages:
                self.page = p
                self.load_page()
        except Exception:
            pass
