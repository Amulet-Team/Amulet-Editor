from PySide6.QtCore import QThread, Slot


class Thread(QThread):
    """
    This is a subclass of the QThread object that adds the behaviour of threading.Thread.
    It also ensures that the Python object survives the life of the Qt thread and gets destroyed after.
    """

    def __init__(self, *QThread_args, target=None, args=(), kwargs=(), **QThread_kwargs):
        super().__init__(*QThread_args, **QThread_kwargs)
        self.__target = target
        self.__args = args
        self.__kwargs = dict(kwargs)

    @Slot(QThread.Priority)
    def start(self, priority: QThread.Priority = QThread.InheritPriority):
        self.finished.connect(lambda: self.deleteLater())
        super().start(priority)

    def run(self):
        self.__target(*self.__args, **self.__kwargs)
