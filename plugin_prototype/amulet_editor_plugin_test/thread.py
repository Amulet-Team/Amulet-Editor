from typing import Callable
from PySide6.QtCore import QThread, QObject, Slot, Signal
from PySide6.QtGui import QGuiApplication


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


class InvokeMethod(QObject):
    """
    Run a function in the main thread.
    This will return once the function is finished.
    """

    # https://stackoverflow.com/questions/68137719/easy-way-to-call-a-function-on-the-main-thread-in-qt-pyside2
    def __init__(self, method: Callable[[], None]):
        """
        Invokes a method on the main thread. Taking care of garbage collection "bugs".
        """
        super().__init__()
        self.moveToThread(QGuiApplication.instance().thread())
        self.setParent(QGuiApplication.instance())
        self.__method = method
        self.__called.connect(self.__execute)
        self.__called.emit()

    __called = Signal()

    @Slot()
    def __execute(self):
        self.__method()
        # trigger garbage collector
        self.setParent(None)
