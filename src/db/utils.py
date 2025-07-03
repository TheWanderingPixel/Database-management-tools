import sys
import os

def resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容开发环境和PyInstaller打包后。
    :param relative_path: 相对路径（如 'res/img/favicon.ico'）
    :return: 绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), '..', relative_path)

def data_path(filename):
    """
    获取数据文件路径：
    - 开发环境：项目根目录下 src/res/data/filename
    - 打包环境：用户主目录下 数据库管理软件/res/data/filename
    """
    if hasattr(sys, '_MEIPASS'):
        base = os.path.join(os.path.expanduser('~'), '数据库管理软件', 'res', 'data')
        if not os.path.exists(base):
            os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)
    # 开发环境
    return os.path.join(os.path.dirname(__file__), '..', 'res', 'data', filename) 