from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import matplotlib
from PyQt5.QtGui import QIcon

class VisualizeDialog(QDialog):
    def __init__(self, table_name, fields, data, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon('favicon.ico'))
        self.setWindowTitle(f'可视化 - {table_name}')
        self.resize(600, 500)
        self.fields = fields
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # 字段选择
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel('字段:'))
        self.field_combo = QComboBox()
        self.field_combo.addItems(self.fields)
        field_layout.addWidget(self.field_combo)
        # 图表类型选择
        field_layout.addWidget(QLabel('图表类型:'))
        self.chart_combo = QComboBox()
        self.chart_combo.addItems(['柱状图', '饼图', '折线图'])
        field_layout.addWidget(self.chart_combo)
        layout.addLayout(field_layout)
        # 按钮区
        btn_layout = QHBoxLayout()
        self.plot_btn = QPushButton('绘制')
        self.plot_btn.clicked.connect(self.plot_chart)
        btn_layout.addWidget(self.plot_btn)
        self.export_btn = QPushButton('导出图片')
        self.export_btn.clicked.connect(self.export_image)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        # matplotlib画布
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def plot_chart(self):
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文
        matplotlib.rcParams['axes.unicode_minus'] = False    # 正确显示负号
        field = self.field_combo.currentText()
        chart_type = self.chart_combo.currentText()
        # 统计该字段的分布
        values = [row[self.fields.index(field)] for row in self.data]
        # 简单计数
        unique, counts = np.unique(values, return_counts=True)
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if chart_type == '柱状图':
            ax.bar(unique, counts)
            ax.set_ylabel('计数')
        elif chart_type == '饼图':
            ax.pie(counts, labels=unique, autopct='%1.1f%%')
        elif chart_type == '折线图':
            ax.plot(unique, counts, marker='o')
            ax.set_ylabel('计数')
        ax.set_title(f'{field} 分布')
        self.canvas.draw()

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, '导出图片', '', 'PNG Image (*.png)')
        if not path:
            return
        try:
            self.figure.savefig(path)
            QMessageBox.information(self, '导出成功', f'图片已保存到: {path}')
        except Exception as e:
            QMessageBox.warning(self, '导出失败', str(e))
