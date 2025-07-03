from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from db.utils import resource_path


class MasterPasswordDialog(QDialog):
    def __init__(self, mode='set', parent=None):
        super().__init__(parent)
        icon_path = resource_path('res/img/favicon.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('主密码' if mode == 'input' else '设置主密码')
        self.resize(380, 220)
        self.mode = mode
        self.password = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel('数据库管理工具')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        tip = QLabel('为保障数据安全，请输入主密码' if self.mode == 'input' else '首次使用，请设置主密码')
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet('color: #666; margin-bottom: 8px;')
        layout.addWidget(tip)
        layout.addSpacing(8)
        layout.addWidget(QLabel('主密码：'))
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pwd_edit)
        if self.mode == 'set':
            layout.addWidget(QLabel('确认主密码：'))
            self.pwd2_edit = QLineEdit()
            self.pwd2_edit.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.pwd2_edit)
        layout.addSpacing(8)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_btn = QPushButton('确定')
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def accept(self):
        pwd = self.pwd_edit.text()
        if not pwd or len(pwd) < 4:
            QMessageBox.warning(self, '错误', '主密码不能为空且不少于4位')
            return
        if self.mode == 'set':
            pwd2 = self.pwd2_edit.text()
            if pwd != pwd2:
                QMessageBox.warning(self, '错误', '两次输入的主密码不一致')
                return
        self.password = pwd
        super().accept()
