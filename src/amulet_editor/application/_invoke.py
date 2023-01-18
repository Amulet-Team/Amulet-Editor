from __future__ import annotations
from typing import TypeVar, Callable
from PySide6.QtCore import Slot, Signal, QObject, Qt
from . import _app

from runtime_final import final


T = TypeVar("T")


@final
class InvokeMethod(QObject):
    def __init__(self):
        """
        Invokes a method on the main thread. Taking care of garbage collection "bugs".
        """
        super().__init__()
        self.__method = None
        self.__return = None

    @classmethod
    def invoke(cls, method: Callable[[], T]) -> T:
        """
        Invoke a method in the main thread and optionally get the return value in a callback.

        :param app: The instance of the QApplication
        :param method: The method to be called in the main thread.
        :return: The method return value.
        """
        self = cls()
        self.__method = method
        self.__return = None
        self.start_signal.connect(
            self.execute,
            Qt.DirectConnection
            if _app.app.thread() is self.thread()
            else Qt.BlockingQueuedConnection,
        )
        # Move to the application thread
        self.moveToThread(_app.app.thread())
        self.setParent(_app.app)
        # Connect slots and start execute

        self.start_signal.emit()
        self.setParent(None)
        return self.__return

    start_signal = Signal()

    @Slot()
    def execute(self):
        self.__return = self.__method()


invoke = InvokeMethod.invoke
