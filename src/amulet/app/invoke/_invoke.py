from __future__ import annotations
from typing import TypeVar, Callable, Generic, Any

from PySide6.QtCore import Signal, QObject, Qt, QThread, QCoreApplication, QTimer

from runtime_final import final

T = TypeVar("T")


@final
class Promise(QObject, Generic[T]):
    """
    A class to execute a function in a QObject's thread.

    >>> func: Callable[[], Any]
    >>> parent: QObject
    >>> promise = Promise(
    >>>     func,  # The function to run
    >>>     parent,  # The QObject to get the thread from. Use QCoreApplication.instance() to run on the main thread.
    >>>     Qt.ConnectionType.QueuedConnection  # The connection type to use.
    >>> )
    >>> def on_finished() -> None:
    >>>     result = promise.result()
    >>> promise.finished.connect(on_finished)  # Connect a function to run when the result is ready.
    >>> promise.start()  # Start executing the function
    """

    __func: Callable[[], Any]
    __finished: bool
    __return: T
    __exception: BaseException | None

    def __init__(
        self, func: Callable[[], T], parent: QObject, connection_type: Qt.ConnectionType
    ) -> None:
        """
        Construct a new promise

        :param func: The function to run. The result can be accessed by calling :meth:`result` when the function is finished.
        :param parent: The QObject to get the thread from. Use QCoreApplication.instance() to run on the main thread.
        :param connection_type: The Qt.ConnectionType to control the behaviour of :meth:`start`.
            AutoConnection automatically picks DirectConnection or QueuedConnection depending on the calling thread.
            DirectConnection will block the calling thread until the function is finished. This can only be used if :meth:`start` is called from the same thread as parent.
            QueuedConnection will add the function to the thread's event queue and return immediately.
            BlockingQueuedConnection is a blocking form of QueuedConnection. It can only be used if :meth:`start` is called from a different thread to parent.
        """
        super().__init__()

        # Move to the thread
        self.moveToThread(parent.thread())
        self.setParent(parent)

        # Connect slot
        self._start.connect(self._execute, connection_type)

        self.__func = func
        self.__finished = False
        self.__exception = None

    _start = Signal()

    def start(self) -> None:
        """
        Start the function execution.
        Depending on the connection type, this may block until the function is finished or return immediately.
        """
        self._start.emit()

    def _execute(self) -> None:
        try:
            self.__return = self.__func()
        except BaseException as e:
            self.__exception = e
        self.__finished = True
        self.finished.emit()
        # Clear parent
        self.setParent(None)

    finished = Signal()

    def is_finished(self) -> bool:
        """Has the function finished executing?"""
        return self.__finished

    def result(self) -> T:
        """Get the return value or re-raise the exception."""
        if not self.__finished:
            raise RuntimeError("Method has not finished.")
        if self.__exception is not None:
            raise self.__exception
        return self.__return


def _get_parent(parent: QObject | None) -> QObject:
    if parent is None:
        # Default to the app if not defined
        parent = QCoreApplication.instance()
        if parent is None:
            raise RuntimeError("The application instance does not exist.")
    return parent


def invoke(func: Callable[[], T], parent: QObject | None = None) -> T:
    """
    Invoke a method and get the return value in a callback.
    This is useful for calling a method across threads.

    :param func: The function or method to be called.
    :param parent: The object to be used as the parent and from which the thread is found. If undefined, defaults to the app instance.
    :return: The method return value.
    """
    parent = _get_parent(parent)

    # If this is the target thread then just call the method
    if QThread.currentThread() is parent.thread():
        return func()

    # Create the instance
    promise = Promise(func, parent, Qt.ConnectionType.BlockingQueuedConnection)
    promise.start()
    return promise.result()


def enqueue(func: Callable[[], Any], parent: QObject | None = None) -> None:
    """
    Enqueue a function in the parent's thread event queue.
    Returns immediately and runs asynchronously.

    :param func: The function to be called.
    :param parent: The object to be used as the parent and from which the thread is found. If undefined, defaults to the app instance.
    :return: The function return value.
    """
    parent = _get_parent(parent)

    QTimer.singleShot(0, parent, func)
