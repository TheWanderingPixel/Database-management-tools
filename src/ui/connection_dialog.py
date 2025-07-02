from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QWidget)
from PyQt5.QtCore import Qt
import os
from db.mysql_client import MySQLClient
from db.sqlite_client import SQLiteClient
from .thread_worker import WorkerThread

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建/编辑数据库连接')
        self.resize(400, 300)
        self.conn_info = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 数据库类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('数据库类型:'))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['MySQL', 'SQLite'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # MySQL参数
        self.mysql_widget = QWidget()
        mysql_layout = QVBoxLayout()
        self.host_edit = QLineEdit('localhost')
        self.port_edit = QLineEdit('3306')
        self.user_edit = QLineEdit('root')
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.db_edit = QLineEdit()
        mysql_layout.addWidget(QLabel('主机:'))
        mysql_layout.addWidget(self.host_edit)
        mysql_layout.addWidget(QLabel('端口:'))
        mysql_layout.addWidget(self.port_edit)
        mysql_layout.addWidget(QLabel('用户名:'))
        mysql_layout.addWidget(self.user_edit)
        mysql_layout.addWidget(QLabel('密码:'))
        mysql_layout.addWidget(self.pwd_edit)
        mysql_layout.addWidget(QLabel('数据库名(可选):'))
        mysql_layout.addWidget(self.db_edit)
        self.mysql_widget.setLayout(mysql_layout)

        # SQLite参数
        self.sqlite_widget = QWidget()
        sqlite_layout = QHBoxLayout()
        self.sqlite_path_edit = QLineEdit()
        self.sqlite_browse_btn = QPushButton('选择文件')
        self.sqlite_browse_btn.clicked.connect(self.browse_sqlite_file)
        sqlite_layout.addWidget(self.sqlite_path_edit)
        sqlite_layout.addWidget(self.sqlite_browse_btn)
        self.sqlite_widget.setLayout(sqlite_layout)

        layout.addWidget(self.mysql_widget)
        layout.addWidget(self.sqlite_widget)

        # 测试连接和确定/取消按钮
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton('测试连接')
        self.test_btn.clicked.connect(self.test_connection)
        self.ok_btn = QPushButton('确定')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, db_type):
        self.mysql_widget.setVisible(db_type == 'MySQL')
        self.sqlite_widget.setVisible(db_type == 'SQLite')

    def browse_sqlite_file(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择SQLite数据库文件', os.getcwd(), 'SQLite Files (*.db *.sqlite);;All Files (*)')
        if path:
            self.sqlite_path_edit.setText(path)

    def test_connection(self):
        db_type = self.type_combo.currentText()
        if db_type == 'MySQL':
            params = {
                'host': self.host_edit.text(),
                'port': int(self.port_edit.text()),
                'user': self.user_edit.text(),
                'password': self.pwd_edit.text(),
                'database': self.db_edit.text() or None
            }
            def do_test():
                client = MySQLClient(**params)
                return client.test_connection()
        elif db_type == 'SQLite':
            db_path = self.sqlite_path_edit.text()
            def do_test():
                client = SQLiteClient(db_path)
                return client.test_connection()
        else:
            QMessageBox.warning(self, '错误', '不支持的数据库类型')
            return

        self.test_btn.setEnabled(False)
        self.thread = WorkerThread(do_test)
        self.thread.finished.connect(self.on_test_connection_result)
        self.thread.start()

    def on_test_connection_result(self, result, error):
        self.test_btn.setEnabled(True)
        if error is not None:
            QMessageBox.warning(self, '测试连接', str(error))
        else:
            ok, msg = result
            if ok:
                QMessageBox.information(self, '测试连接', msg)
            else:
                QMessageBox.warning(self, '测试连接', msg)

    def get_connection_info(self):
        db_type = self.type_combo.currentText()
        if db_type == 'MySQL':
            return {
                'type': 'MySQL',
                'host': self.host_edit.text(),
                'port': int(self.port_edit.text()),
                'user': self.user_edit.text(),
                'password': self.pwd_edit.text(),
                'database': self.db_edit.text() or None
            }
        elif db_type == 'SQLite':
            return {
                'type': 'SQLite',
                'db_path': self.sqlite_path_edit.text()
            }
        return None

    def accept(self):
        info = self.get_connection_info()
        if info is None:
            QMessageBox.warning(self, '错误', '请填写完整的连接信息')
            return
        self.conn_info = info
        super().accept() 