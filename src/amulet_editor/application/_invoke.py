from __future__ import annotations
from typing import TypeVar, Callable, Generic
from PySide6.QtCore import Slot, Signal, QObject, Qt, QThread
from PySide6.QtGui import QGuiApplication

from runtime_final import final


T = TypeVar("T")


@final
class InvokeMethod(QObject, Generic[T]):
    __method: Callable[[], T]
    __return: T
    __exception: BaseException | None

    def __init__(self) -> None:
        super().__init__()
        self.__exception: BaseException | None = None

    @classmethod
    def invoke(cls, method: Callable[[], T], parent: QObject | None = None) -> T:
        """
        Invoke a method and get the return value in a callback.
        This is useful for calling a method across threads.

        :param method: The function or method to be called.
        :param parent: The object to be used as the parent and from which the thread is found. If undefined uses the app instance.
        :return: The method return value.
        """
        # Create the instance
        self = cls()

        # Set the method for access later
        self.__method = method

        if parent is None:
            # Default to the app if not defined
            parent = QGuiApplication.instance()
            assert parent is not None

        # Get the thread from the object
        thread = parent.thread()

        # Move to the thread
        self.moveToThread(thread)
        self.setParent(parent)

        # Connect slot
        self.start_signal.connect(
            self.execute,
            (
                Qt.ConnectionType.DirectConnection
                if thread is QThread.currentThread()
                else Qt.ConnectionType.BlockingQueuedConnection
            ),
        )

        # Start execute. This will block execution of this function until it is finished.
        self.start_signal.emit()

        # Clear parent
        self.setParent(None)

        # Process return
        if self.__exception is None:
            return self.__return
        else:
            raise self.__exception

    start_signal = Signal()

    @Slot()
    def execute(self) -> None:
        try:
            self.__return = self.__method()
        except BaseException as e:
            self.__exception = e


invoke = InvokeMethod.invoke
