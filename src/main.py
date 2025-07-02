import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QTabWidget, QTreeWidget, QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, QLabel, QStatusBar,
    QPushButton, QHBoxLayout, QMenu, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox, QInputDialog, QFileDialog, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QIcon
from db.connection_manager import ConnectionManager, KEY_FILE
from ui.connection_dialog import ConnectionDialog
from ui.sql_editor import SQLEditor
from ui.visualize_dialog import VisualizeDialog
from ui.table_data_viewer import TableDataViewer
from ui.master_password_dialog import MasterPasswordDialog
import csv
import json
import shutil
from datetime import datetime
import os
import traceback

class WelcomeWidget(QWidget):
    def __init__(self, tab_widget, parent=None):
        super().__init__(parent)
        self.tab_widget = tab_widget
        layout = QVBoxLayout(self)
        label = QLabel('<h2>欢迎使用数据库管理工具</h2>'
                       '<p>本工具支持多种数据库的连接、管理、可视化与数据操作。</p>'
                       '<ul>'
                       '<li>左侧可管理数据库连接</li>'
                       '<li>右键表节点可导入/导出/可视化/分页浏览数据</li>'
                       '<li>右上菜单可切换主题、导入导出配置、备份恢复等</li>'
                       '<li>如需帮助请查看"帮助-使用说明"</li>'
                       '</ul>')
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        close_btn = QPushButton('关闭欢迎页')
        close_btn.clicked.connect(self.close_welcome)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    def close_welcome(self):
        idx = self.tab_widget.indexOf(self)
        if idx != -1:
            self.tab_widget.removeTab(idx)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_conn_manager()
        self.setWindowTitle('数据库管理工具')
        self.resize(1200, 800)
        self.init_ui()

    def _init_conn_manager(self):
        self.conn_manager = ConnectionManager()

    def init_ui(self):
        # 菜单栏
        menubar = self.menuBar()
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        import_cfg_action = QAction(QIcon(), '导入配置', self)
        import_cfg_action.setShortcut('Ctrl+I')
        export_cfg_action = QAction(QIcon(), '导出配置', self)
        export_cfg_action.setShortcut('Ctrl+E')
        backup_action = QAction(QIcon(), '备份数据', self)
        restore_action = QAction(QIcon(), '恢复数据', self)
        file_menu.addAction(import_cfg_action)
        file_menu.addAction(export_cfg_action)
        file_menu.addSeparator()
        file_menu.addAction(backup_action)
        file_menu.addAction(restore_action)
        file_menu.addSeparator()
        exit_action = QAction(QIcon(), '退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 数据库菜单
        db_menu = menubar.addMenu('数据库')
        new_conn_action = QAction(QIcon(), '新建连接', self)
        new_conn_action.setShortcut('Ctrl+N')
        new_conn_action.triggered.connect(self.add_connection)
        refresh_conn_action = QAction(QIcon(), '刷新连接', self)
        refresh_conn_action.setShortcut('F5')
        refresh_conn_action.triggered.connect(self.refresh_db_tree)
        open_sql_action = QAction(QIcon(), '打开SQL编辑器', self)
        open_sql_action.setShortcut('Ctrl+T')
        open_sql_action.triggered.connect(self.open_sql_editor_tab)
        db_menu.addAction(new_conn_action)
        db_menu.addAction(open_sql_action)
        db_menu.addAction(refresh_conn_action)

        # 主题菜单
        theme_menu = menubar.addMenu('主题')
        light_action = QAction('明亮', self)
        dark_action = QAction('暗色', self)
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)
        light_action.triggered.connect(lambda: self.set_theme('light'))
        dark_action.triggered.connect(lambda: self.set_theme('dark'))

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        doc_action = QAction(QIcon(), '使用说明', self)
        about_action = QAction(QIcon(), '关于', self)
        doc_action.triggered.connect(lambda: self.show_info('使用说明', '请参考项目README或在线文档。'))
        about_action.triggered.connect(lambda: self.show_info('关于', '数据库管理工具\n版本 1.0\n作者：xsy72'))
        help_menu.addAction(doc_action)
        help_menu.addAction(about_action)

        # 文件菜单功能绑定
        import_cfg_action.triggered.connect(self.import_config)
        export_cfg_action.triggered.connect(self.export_config)
        backup_action.triggered.connect(self.backup_data)
        restore_action.triggered.connect(self.restore_data)

        # 工具栏
        toolbar = self.addToolBar('主工具栏')
        toolbar.addAction(exit_action)

        # 状态栏
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage('准备就绪')

        # 左侧：数据库对象树 + 新建连接按钮
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.add_conn_btn = QPushButton('新建连接')
        self.add_conn_btn.clicked.connect(self.add_connection)
        left_layout.addWidget(self.add_conn_btn)
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel('数据库连接')
        self.db_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.db_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.db_tree.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.db_tree)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(2)
        self.refresh_db_tree()

        # 右侧：多标签页
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tabs.addTab(WelcomeWidget(self.tabs), '欢迎')
        self.add_sql_editor_tab()

        # 主体布局
        splitter = QSplitter()
        splitter.addWidget(left_widget)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([250, 950])

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        # 支持Ctrl+Tab切换标签页
        self.tabs.installEventFilter(self)

    def refresh_db_tree(self):
        self.db_tree.clear()
        for idx, conn in enumerate(self.conn_manager.get_connections()):
            label = f"[{conn['type']}] "
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                # 判断是否指定了database
                if conn.get('database'):
                    dbs = [conn['database']]
                else:
                    dbs = client.get_databases()
                for dbname in dbs:
                    db_item = QTreeWidgetItem(self.db_tree, [f"{label}{dbname}"])
                    db_item.setData(0, Qt.UserRole, {'conn_idx': idx, 'database': dbname})
                    db_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            elif conn['type'] == 'SQLite':
                label += conn['db_path']
                item = QTreeWidgetItem(self.db_tree, [label])
                item.setData(0, Qt.UserRole, idx)
                item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        self.db_tree.expandAll()

    def get_conn_index(self, idx):
        if idx is None:
            return None
        if isinstance(idx, dict) and 'conn_idx' in idx:
            return idx['conn_idx']
        return idx

    def on_tree_item_clicked(self, item, column):
        idx = item.data(0, Qt.UserRole)
        # 如果是表节点（有'table'键），只显示表结构，不再展开
        if isinstance(idx, dict) and 'conn_idx' in idx and 'table' in idx:
            dbname = idx.get('database', None)
            if dbname:
                self.current_db = dbname
            self.show_table_schema(self.get_conn_index(idx), idx['table'])
            return
        # 只为数据库节点加载表列表，且只加载一次
        if isinstance(idx, dict) and 'conn_idx' in idx and 'database' in idx:
            if item.childCount() > 0:
                return  # 已加载过表，避免递归
            conn = self.conn_manager.get_connection(self.get_conn_index(idx['conn_idx']))
            if not conn:
                return
            from db.mysql_client import MySQLClient
            client = MySQLClient(
                host=conn['host'],
                port=conn['port'],
                user=conn['user'],
                password=conn['password'],
                database=idx['database']
            )
            tables = client.get_tables()
            for t in tables:
                table_item = QTreeWidgetItem(item, [t])
                table_item.setData(0, Qt.UserRole, {'conn_idx': idx['conn_idx'], 'table': t, 'database': idx['database']})
            item.setExpanded(True)
            self.current_db = idx['database']
            for i in range(self.tabs.count()):
                w = self.tabs.widget(i)
                if hasattr(w, 'current_db_label'):
                    w.current_db_label.setText(f'当前数据库：{idx["database"]}')
                    w.current_db = idx['database']
            return
        # 其他节点逻辑保持不变
        if isinstance(idx, int) and item.childCount() == 0:
            conn = self.conn_manager.get_connection(self.get_conn_index(idx))
            if not conn:
                return
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                tables = client.get_tables()
            elif conn['type'] == 'SQLite':
                from db.sqlite_client import SQLiteClient
                client = SQLiteClient(conn['db_path'])
                tables = client.get_tables()
            else:
                tables = []
            for t in tables:
                table_item = QTreeWidgetItem(item, [t])
                table_item.setData(0, Qt.UserRole, {'conn_idx': idx, 'table': t})
            item.setExpanded(True)

    def switch_to_tab(self, tab_title):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_title:
                self.tabs.setCurrentIndex(i)
                return True
        return False

    def show_table_schema(self, conn_idx, table_name):
        tab_title = f"结构:{table_name}"
        # 若tab已存在，先关闭再新建，确保每次都刷新
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_title:
                self.tabs.removeTab(i)
                break
        conn = self.conn_manager.get_connection(self.get_conn_index(conn_idx))
        if not conn:
            return
        if conn['type'] == 'MySQL':
            from db.mysql_client import MySQLClient
            client = MySQLClient(
                host=conn['host'],
                port=conn['port'],
                user=conn['user'],
                password=conn['password'],
                database=conn['database']
            )
            schema = client.get_table_schema(table_name)
        elif conn['type'] == 'SQLite':
            from db.sqlite_client import SQLiteClient
            client = SQLiteClient(conn['db_path'])
            schema = client.get_table_schema(table_name)
        else:
            schema = []
        # 展示到新标签页
        tab = QTableWidget()
        if schema:
            tab.setColumnCount(len(schema[0]))
            tab.setRowCount(len(schema))
            tab.setHorizontalHeaderLabels(list(schema[0].keys()))
            for row, coldata in enumerate(schema):
                for col, key in enumerate(schema[0].keys()):
                    tab.setItem(row, col, QTableWidgetItem(str(coldata[key])))
        else:
            tab.setRowCount(0)
            tab.setColumnCount(1)
            tab.setHorizontalHeaderLabels(['无数据'])
        self.tabs.addTab(tab, tab_title)
        self.tabs.setCurrentWidget(tab)

    def add_connection(self):
        dlg = ConnectionDialog(self)
        if dlg.exec_() == dlg.Accepted and dlg.conn_info:
            self.conn_manager.add_connection(dlg.conn_info)
            self.refresh_db_tree()
            self.log_message('连接添加成功')

    def show_tree_context_menu(self, pos: QPoint):
        item = self.db_tree.itemAt(pos)
        if not item:
            return
        idx = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        # 判断是否为表节点
        is_table = isinstance(idx, dict) and 'conn_idx' in idx and 'table' in idx
        if is_table:
            view_action = menu.addAction('查看数据')
            export_action = menu.addAction('导出数据')
            import_action = menu.addAction('导入数据')
            visualize_action = menu.addAction('可视化')
            menu.addSeparator()
        edit_action = menu.addAction('编辑') if not is_table else None
        delete_action = menu.addAction('删除') if not is_table else None
        test_action = menu.addAction('测试连接') if not is_table else None
        action = menu.exec_(self.db_tree.viewport().mapToGlobal(pos))
        if is_table:
            if action == view_action:
                self.view_table_data(self.get_conn_index(idx), idx['table'])
            elif action == export_action:
                self.export_table_to_csv(self.get_conn_index(idx), idx['table'])
            elif action == import_action:
                self.import_table_from_csv(self.get_conn_index(idx), idx['table'])
            elif action == visualize_action:
                self.visualize_table(self.get_conn_index(idx), idx['table'])
        else:
            if action == edit_action:
                self.edit_connection(self.get_conn_index(idx))
            elif action == delete_action:
                self.delete_connection(self.get_conn_index(idx))
            elif action == test_action:
                self.test_connection(self.get_conn_index(idx))

    def edit_connection(self, idx):
        conn = self.conn_manager.get_connection(self.get_conn_index(idx))
        if not conn:
            return
        dlg = ConnectionDialog(self)
        # 预填充数据
        if conn['type'] == 'MySQL':
            dlg.type_combo.setCurrentText('MySQL')
            dlg.host_edit.setText(conn.get('host', ''))
            dlg.port_edit.setText(str(conn.get('port', '3306')))
            dlg.user_edit.setText(conn.get('user', ''))
            dlg.pwd_edit.setText(conn.get('password', ''))
            dlg.db_edit.setText(conn.get('database', ''))
        elif conn['type'] == 'SQLite':
            dlg.type_combo.setCurrentText('SQLite')
            dlg.sqlite_path_edit.setText(conn.get('db_path', ''))
        if dlg.exec_() == dlg.Accepted and dlg.conn_info:
            self.conn_manager.update_connection(idx, dlg.conn_info)
            self.refresh_db_tree()
            self.log_message('连接编辑成功')

    def delete_connection(self, idx):
        reply = QMessageBox.question(self, '确认删除', '确定要删除该连接吗？', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.conn_manager.remove_connection(idx)
            self.refresh_db_tree()
            self.log_message('连接删除成功')

    def test_connection(self, idx):
        conn = self.conn_manager.get_connection(self.get_conn_index(idx))
        if not conn:
            return
        if conn['type'] == 'MySQL':
            from db.mysql_client import MySQLClient
            client = MySQLClient(
                host=conn['host'],
                port=conn['port'],
                user=conn['user'],
                password=conn['password'],
                database=conn['database']
            )
            ok, msg = client.test_connection()
        elif conn['type'] == 'SQLite':
            from db.sqlite_client import SQLiteClient
            client = SQLiteClient(conn['db_path'])
            ok, msg = client.test_connection()
        else:
            ok, msg = False, '暂不支持该类型'
        QMessageBox.information(self, '测试连接', msg)
        self.log_message(f'测试连接{"成功" if ok else "失败"}: {msg}')

    def add_sql_editor_tab(self):
        tab_title = 'SQL编辑器'
        if self.switch_to_tab(tab_title):
            return
        editor = SQLEditor()
        db_label = QLabel('当前数据库：')
        editor.current_db_label = db_label
        conn_select_layout = QHBoxLayout()
        conn_label = QLabel('连接:')
        conn_select_layout.addWidget(conn_label)
        conn_combo = QComboBox()
        conn_list = self.conn_manager.get_connections()
        for idx, conn in enumerate(conn_list):
            if conn['type'] == 'MySQL':
                label = f"[{conn['type']}] {conn['user']}@{conn['host']}:{conn['port']}/{conn['database']}"
            elif conn['type'] == 'SQLite':
                label = f"[{conn['type']}] {conn['db_path']}"
            else:
                label = f"[{conn['type']}]"
            conn_combo.addItem(label, idx)
        editor.conn_combo = conn_combo
        conn_select_layout.addWidget(conn_combo)
        conn_select_layout.addWidget(db_label)
        conn_select_layout.addStretch()
        editor.layout().insertLayout(0, conn_select_layout)
        editor.current_db = None
        def update_conn_combo_database(dbname):
            # 只对MySQL类型生效
            idx = conn_combo.currentIndex()
            if idx < 0:
                return
            conn = self.conn_manager.get_connections()[idx]
            if conn['type'] == 'MySQL':
                label = f"[{conn['type']}] {conn['user']}@{conn['host']}:{conn['port']}/{dbname}"
                conn_combo.setItemText(idx, label)
        def exec_sql():
            if conn_combo.count() == 0:
                editor.result_label.setText('无可用连接，请先新建数据库连接')
                editor.set_result([],[])
                return
            idx = conn_combo.currentData()
            if idx is None:
                editor.result_label.setText('未选择连接')
                editor.set_result([],[])
                return
            # 新增：优先获取选中内容
            selected_sql = editor.sql_edit.textCursor().selectedText().strip()
            if selected_sql:
                sql = selected_sql
            else:
                sql = editor.sql_edit.toPlainText().strip()
            if not sql:
                editor.result_label.setText('请输入SQL语句')
                editor.set_result([],[])
                return
            conn_idx = self.get_conn_index(idx)
            if conn_idx is None:
                editor.result_label.setText('未选择连接')
                editor.set_result([],[])
                return
            conn = self.conn_manager.get_connection(conn_idx)
            if not conn:
                editor.result_label.setText('未选择连接')
                editor.set_result([],[])
                return
            # 自动加USE语句（仅MySQL）
            sql_to_run = sql
            if conn['type'] == 'MySQL' and hasattr(editor, 'current_db') and editor.current_db:
                # 若SQL本身未以USE开头，则加上
                if not sql.strip().lower().startswith('use '):
                    sql_to_run = f"USE `{editor.current_db}`;\n" + sql
            else:
                sql_to_run = sql
            sql_statements = [s.strip() for s in sql_to_run.split(';') if s.strip()]
            try:
                if conn['type'] == 'MySQL':
                    from db.mysql_client import MySQLClient
                    client = MySQLClient(
                        host=conn['host'],
                        port=conn['port'],
                        user=conn['user'],
                        password=conn['password'],
                        database=conn['database']
                    )
                    dbconn = client.connect()
                    cursor = dbconn.cursor()
                    last_result = None
                    for i, statement in enumerate(sql_statements):
                        try:
                            if statement.strip().lower().startswith('use '):
                                dbname = statement.strip()[4:].strip(' ;')
                                cursor.execute(statement)
                                editor.current_db = dbname
                                db_label.setText(f'当前数据库：{dbname}')
                                update_conn_combo_database(dbname)
                                continue
                            cursor.execute(statement)
                            if cursor.description:
                                headers = [d[0] for d in cursor.description]
                                rows = cursor.fetchall()
                                last_result = (headers, rows, f'第{i+1}条: 共{len(rows)}行')
                            else:
                                dbconn.commit()
                                last_result = ([], [], f'第{i+1}条: 执行成功，无返回结果')
                        except Exception as e:
                            editor.result_label.setText(f'第{i+1}条SQL执行出错: {e}')
                            editor.set_result([],[])
                            client.close()
                            return
                    if last_result:
                        headers, rows, msg = last_result
                        editor.set_result(headers, rows)
                        editor.result_label.setText(msg)
                    client.close()
                elif conn['type'] == 'SQLite':
                    from db.sqlite_client import SQLiteClient
                    client = SQLiteClient(conn['db_path'])
                    dbconn = client.connect()
                    cursor = dbconn.cursor()
                    last_result = None
                    for i, statement in enumerate(sql_statements):
                        try:
                            cursor.execute(statement)
                            if cursor.description:
                                headers = [d[0] for d in cursor.description]
                                rows = cursor.fetchall()
                                last_result = (headers, rows, f'第{i+1}条: 共{len(rows)}行')
                            else:
                                dbconn.commit()
                                last_result = ([], [], f'第{i+1}条: 执行成功，无返回结果')
                        except Exception as e:
                            editor.result_label.setText(f'第{i+1}条SQL执行出错: {e}')
                            editor.set_result([],[])
                            client.close()
                            return
                    if last_result:
                        headers, rows, msg = last_result
                        editor.set_result(headers, rows)
                        editor.result_label.setText(msg)
                    client.close()
                else:
                    editor.result_label.setText('暂不支持该类型')
                    editor.set_result([],[])
            except Exception as e:
                editor.result_label.setText(f'执行出错: {e}')
                editor.set_result([],[])
            self.log_message('SQL执行成功')
        editor.exec_btn.clicked.connect(exec_sql)
        self.tabs.addTab(editor, tab_title)
        self.tabs.setCurrentWidget(editor)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def show_tab_context_menu(self, pos):
        tab_index = self.tabs.tabBar().tabAt(pos)
        if tab_index < 0:
            return
        menu = QMenu(self)
        close_action = menu.addAction('关闭')
        close_others_action = menu.addAction('关闭其他')
        rename_action = menu.addAction('重命名')
        action = menu.exec_(self.tabs.tabBar().mapToGlobal(pos))
        if action == close_action:
            self.close_tab(tab_index)
        elif action == close_others_action:
            for i in reversed(range(self.tabs.count())):
                if i != tab_index and i != 0:
                    self.tabs.removeTab(i)
        elif action == rename_action:
            old_name = self.tabs.tabText(tab_index)
            new_name, ok = QInputDialog.getText(self, '重命名标签页', '新名称：', text=old_name)
            if ok and new_name:
                self.tabs.setTabText(tab_index, new_name)

    def eventFilter(self, obj, event):
        if obj == self.tabs and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Tab:
                idx = self.tabs.currentIndex()
                count = self.tabs.count()
                self.tabs.setCurrentIndex((idx + 1) % count)
                return True
        return super().eventFilter(obj, event)

    def set_theme(self, theme):
        if theme == 'dark':
            # 优化后的暗色QSS，提升SQL编辑区可读性
            qss = """
            QWidget { background: #232629; color: #F0F0F0; }
            QLineEdit, QTextEdit, QPlainTextEdit { background: #232629; color: #F0F0F0; selection-background-color: #44475a; selection-color: #ffffff; }
            QPlainTextEdit { border: 1px solid #444; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #31363b; color: #F0F0F0; padding: 6px; }
            QTabBar::tab:selected { background: #232629; }
            QPushButton { background: #31363b; color: #F0F0F0; border: 1px solid #444; }
            QMenu { background: #31363b; color: #F0F0F0; }
            QTreeWidget, QTableWidget { background: #232629; color: #F0F0F0; }
            QHeaderView::section { background: #31363b; color: #F0F0F0; }
            """
            self.setStyleSheet(qss)
        else:
            self.setStyleSheet("")

        # 同步设置所有SQL编辑器的暗黑模式
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            try:
                from ui.sql_editor import SQLEditor
                if isinstance(widget, SQLEditor):
                    widget.sql_edit.set_dark_mode(theme == 'dark')
            except Exception:
                pass

    def log_message(self, msg):
        self.statusBar().showMessage(msg, 5000)

    def export_table_to_csv(self, conn_idx, table_name):
        conn = self.conn_manager.get_connection(self.get_conn_index(conn_idx))
        if not conn:
            self.log_message('连接信息无效')
            QMessageBox.warning(self, '导出失败', '连接信息无效')
            return
        path, _ = QFileDialog.getSaveFileName(self, f'导出表[{table_name}]为CSV', f'{table_name}.csv', 'CSV Files (*.csv)')
        if not path:
            self.log_message('未选择导出路径')
            QMessageBox.information(self, '导出取消', '未选择导出路径')
            return
        try:
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM `{table_name}`')
                rows = cursor.fetchall()
                headers = [d[0] for d in cursor.description]
                client.close()
            elif conn['type'] == 'SQLite':
                from db.sqlite_client import SQLiteClient
                client = SQLiteClient(conn['db_path'])
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                headers = [d[0] for d in cursor.description]
                client.close()
            else:
                self.log_message('暂不支持该类型')
                QMessageBox.warning(self, '导出失败', '暂不支持该类型')
                return
            if not headers:
                self.log_message('表无字段，无法导出')
                QMessageBox.information(self, '导出提示', '表无字段，无法导出')
                return
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                if rows:
                    writer.writerows(rows)
            self.log_message(f'表[{table_name}]已成功导出到 {path}')
            QMessageBox.information(self, '导出成功', f'表[{table_name}]已成功导出到\n{path}')
        except Exception as e:
            self.log_message(f'导出失败: {e}')
            QMessageBox.critical(self, '导出失败', str(e))

    def import_table_from_csv(self, conn_idx, table_name):
        conn = self.conn_manager.get_connection(self.get_conn_index(conn_idx))
        if not conn:
            self.log_message('连接信息无效')
            QMessageBox.warning(self, '导入失败', '连接信息无效')
            return
        path, _ = QFileDialog.getOpenFileName(self, f'导入CSV到表[{table_name}]', '', 'CSV Files (*.csv)')
        if not path:
            self.log_message('未选择CSV文件')
            QMessageBox.information(self, '导入取消', '未选择CSV文件')
            return
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = list(reader)
            if not rows:
                self.log_message('CSV文件无数据')
                QMessageBox.information(self, '导入提示', 'CSV文件无数据')
                return
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                dbconn = client.connect()
                cursor = dbconn.cursor()
                placeholders = ','.join(['%s'] * len(headers))
                columns = ','.join([f"`{h}`" for h in headers])
                sql = f'INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})'
                cursor.executemany(sql, rows)
                dbconn.commit()
                client.close()
            elif conn['type'] == 'SQLite':
                from db.sqlite_client import SQLiteClient
                client = SQLiteClient(conn['db_path'])
                dbconn = client.connect()
                cursor = dbconn.cursor()
                placeholders = ','.join(['?'] * len(headers))
                columns = ','.join([f'"{h}"' for h in headers])
                sql = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
                cursor.executemany(sql, rows)
                dbconn.commit()
                client.close()
            else:
                self.log_message('暂不支持该类型')
                QMessageBox.warning(self, '导入失败', '暂不支持该类型')
                return
            self.log_message(f'CSV数据已成功导入表[{table_name}]，共{len(rows)}行')
            QMessageBox.information(self, '导入成功', f'CSV数据已成功导入表[{table_name}]，共{len(rows)}行')
        except Exception as e:
            self.log_message(f'导入失败: {e}')
            QMessageBox.critical(self, '导入失败', str(e))

    def view_table_data(self, conn_idx, table_name):
        tab_title = f'数据:{table_name}'
        if self.switch_to_tab(tab_title):
            return
        conn = self.conn_manager.get_connection(self.get_conn_index(conn_idx))
        if not conn:
            self.log_message('连接信息无效')
            return
        try:
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM `{table_name}` LIMIT 1')
                headers = [d[0] for d in cursor.description]
                client.close()
                def fetch_page(page, page_size):
                    client2 = MySQLClient(
                        host=conn['host'],
                        port=conn['port'],
                        user=conn['user'],
                        password=conn['password'],
                        database=conn['database']
                    )
                    dbconn2 = client2.connect()
                    cursor2 = dbconn2.cursor()
                    offset = (page-1)*page_size
                    cursor2.execute(f'SELECT * FROM `{table_name}` LIMIT %s OFFSET %s', (page_size, offset))
                    rows = cursor2.fetchall()
                    cursor2.execute(f'SELECT COUNT(*) FROM `{table_name}`')
                    total = cursor2.fetchone()[0]
                    client2.close()
                    return rows, total
                # 获取主键信息
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f"SHOW KEYS FROM `{table_name}` WHERE Key_name = 'PRIMARY'")
                pk_fields = [row[4] for row in cursor.fetchall()]
                client.close()
                db_client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
            elif conn['type'] == 'SQLite':
                from db.sqlite_client import SQLiteClient
                client = SQLiteClient(conn['db_path'])
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 1')
                headers = [d[0] for d in cursor.description]
                client.close()
                def fetch_page(page, page_size):
                    client2 = SQLiteClient(conn['db_path'])
                    dbconn2 = client2.connect()
                    cursor2 = dbconn2.cursor()
                    offset = (page-1)*page_size
                    cursor2.execute(f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?', (page_size, offset))
                    rows = cursor2.fetchall()
                    cursor2.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    total = cursor2.fetchone()[0]
                    client2.close()
                    return rows, total
                # 获取主键信息
                client = SQLiteClient(conn['db_path'])
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                pk_fields = [row[1] for row in cursor.fetchall() if row[5]]
                client.close()
                db_client = SQLiteClient(conn['db_path'])
            else:
                self.log_message('暂不支持该类型')
                return
            viewer = TableDataViewer(headers, fetch_page_callback=fetch_page, parent=self, db_client=db_client, table_name=table_name, pk_fields=pk_fields)
            self.tabs.addTab(viewer, tab_title)
            self.tabs.setCurrentWidget(viewer)
        except Exception as e:
            self.log_message(f'数据浏览失败: {e}')

    def visualize_table(self, conn_idx, table_name):
        tab_title = f'可视化:{table_name}'
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_title:
                self.tabs.setCurrentIndex(i)
                return
        conn = self.conn_manager.get_connection(self.get_conn_index(conn_idx))
        if not conn:
            self.log_message('连接信息无效')
            QMessageBox.warning(self, '可视化失败', '连接信息无效')
            return
        try:
            if conn['type'] == 'MySQL':
                from db.mysql_client import MySQLClient
                client = MySQLClient(
                    host=conn['host'],
                    port=conn['port'],
                    user=conn['user'],
                    password=conn['password'],
                    database=conn['database']
                )
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM `{table_name}`')
                rows = cursor.fetchall()
                headers = [d[0] for d in cursor.description]
                client.close()
            elif conn['type'] == 'SQLite':
                from db.sqlite_client import SQLiteClient
                client = SQLiteClient(conn['db_path'])
                dbconn = client.connect()
                cursor = dbconn.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                headers = [d[0] for d in cursor.description]
                client.close()
            else:
                self.log_message('暂不支持该类型')
                QMessageBox.warning(self, '可视化失败', '暂不支持该类型')
                return
            if not rows:
                QMessageBox.information(self, '可视化提示', '表无数据，无法可视化')
                return
            # 以QWidget方式嵌入tab
            widget = VisualizeDialog(table_name, headers, rows, self)
            self.tabs.addTab(widget, tab_title)
            self.tabs.setCurrentWidget(widget)
        except Exception as e:
            self.log_message(f'可视化失败: {e}')
            QMessageBox.critical(self, '可视化失败', str(e))

    def show_info(self, title, msg):
        if title == '使用说明':
            self.show_help_dialog(msg)
        else:
            QMessageBox.information(self, title, msg)

    def show_help_dialog(self, msg):
        dlg = QDialog(self)
        dlg.setWindowTitle('使用说明')
        dlg.resize(600, 500)
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(self.get_help_text())
        layout.addWidget(text)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        layout.addWidget(btns)
        dlg.exec_()

    def get_help_text(self):
        return (
            '数据库管理工具使用说明\n'
            '--------------------------\n'
            '1. 连接管理：\n'
            '   - 新建连接：菜单栏"数据库-新建连接"或左侧"新建连接"按钮。\n'
            '   - 编辑/删除/测试连接：右键连接节点。\n'
            '2. 数据库对象浏览：\n'
            '   - 点击连接节点展开表列表。\n'
            '3. 表操作：\n'
            '   - 右键表节点可"查看数据""导入数据""导出数据""可视化"。\n'
            '   - 查看数据支持分页浏览。\n'
            '   - 可视化支持柱状图、饼图、折线图，并可导出图片。\n'
            '4. SQL编辑器：\n'
            '   - 右侧"SQL编辑器"标签页，选择连接后可执行SQL语句。\n'
            '5. 主题切换：\n'
            '   - 菜单栏"主题"可切换明亮/暗色。\n'
            '6. 配置与备份：\n'
            '   - 菜单栏"文件"可导入/导出配置、备份/恢复数据。\n'
            '7. 其他：\n'
            '   - 所有操作结果会在底部状态栏提示。\n'
            '   - 更多功能和帮助请参考项目README或联系作者。\n'
        )

    def import_config(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, '导入配置文件', '', '配置文件 (*.json *.enc);;所有文件 (*)')
        if not path:
            return
        try:
            if path.endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # 加密文件，尝试用当前fernet解密
                with open(path, 'rb') as f:
                    enc_data = f.read()
                data = self.conn_manager.fernet.decrypt(enc_data)
                data = json.loads(data.decode('utf-8'))
            if isinstance(data, list):
                self.conn_manager.connections = data
                self.conn_manager.save_connections()
                self.refresh_db_tree()
                self.log_message('配置导入成功')
            else:
                self.log_message('配置文件格式错误')
        except Exception as e:
            self.log_message(f'导入失败: {e}')

    def export_config(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, '导出配置文件', '', '加密配置 (*.enc);;明文JSON (*.json)')
        if not path:
            return
        try:
            if path.endswith('.json'):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.conn_manager.connections, f, ensure_ascii=False, indent=2)
            else:
                data = json.dumps(self.conn_manager.connections, ensure_ascii=False, indent=2).encode('utf-8')
                enc_data = self.conn_manager.fernet.encrypt(data)
                with open(path, 'wb') as f:
                    f.write(enc_data)
            self.log_message('配置导出成功')
        except Exception as e:
            self.log_message(f'导出失败: {e}')

    def backup_data(self):
        from PyQt5.QtWidgets import QFileDialog
        backup_dir = QFileDialog.getExistingDirectory(self, '选择备份目录')
        if not backup_dir:
            return
        try:
            src = os.path.join(os.path.dirname(__file__), 'db', 'connections.json.enc')
            if not os.path.exists(src):
                self.log_message('无加密配置文件可备份')
                return
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            dst = os.path.join(backup_dir, f'connections_backup_{ts}.enc')
            shutil.copy2(src, dst)
            self.log_message(f'备份成功: {dst}')
        except Exception as e:
            self.log_message(f'备份失败: {e}')

    def restore_data(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, '选择备份文件', '', '加密配置 (*.enc)')
        if not path:
            return
        try:
            dst = os.path.join(os.path.dirname(__file__), 'db', 'connections.json.enc')
            shutil.copy2(path, dst)
            self.conn_manager.load_connections()
            self.refresh_db_tree()
            self.log_message('恢复成功')
        except Exception as e:
            self.log_message(f'恢复失败: {e}')

    def open_sql_editor_tab(self):
        self.add_sql_editor_tab()

def main():
    app = QApplication(sys.argv)
    # 主密码流程
    password = None
    is_first = not os.path.exists(KEY_FILE)
    while True:
        if is_first:
            dlg = MasterPasswordDialog(mode='set')
            if dlg.exec_() == dlg.Accepted:
                password = dlg.password
                break
            else:
                return  # 用户取消
        else:
            dlg = MasterPasswordDialog(mode='input')
            if dlg.exec_() == dlg.Accepted:
                password = dlg.password
                break
            else:
                return
    # 初始化主窗口
    try:
        window = MainWindowWithPassword(password)
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, '启动失败', f'错误: {e}\n{traceback.format_exc()}')
        return

class MainWindowWithPassword(MainWindow):
    def __init__(self, password):
        self._password = password
        super().__init__()
        self._init_conn_manager()

    def _init_conn_manager(self):
        self.conn_manager = ConnectionManager(password=self._password)

if __name__ == '__main__':
    main() 