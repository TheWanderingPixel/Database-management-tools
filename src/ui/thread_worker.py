from PyQt5.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    # 任务完成信号，返回结果和错误信息
    finished = pyqtSignal(object, object)  # result, error

    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func  # 传入的耗时函数
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.finished.emit(result, None)
        except Exception as e:
            self.finished.emit(None, e) 