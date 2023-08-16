from __future__ import annotations

from typing import Generic, TypeVar, Callable, Any, Generator, Union
from threading import Lock
from enum import IntEnum
from PySide6.QtCore import QObject, Signal, QThreadPool, SignalInstance
from amulet_editor.data.dev._debug import enable_trace


T = TypeVar("T")
Void = object()


class Promise(QObject, Generic[T]):
    """
    A class to simplify asynchronous function calls.
    A target function is passed in which is run in a new thread.
    The target function is given the promise instance through which it can notify progress changes and text changes.
    The return value from the function is accessible from :meth:`get_return` or if an exception occurred it will be re-raised when :meth:`get_return` is called.
    It can also optionally support canceling by periodically checking is_cancel_requested and raising :attr:`OperationCanceled` to signify its acceptance of the cancel.
    """

    class Data:
        def __init__(
            self,
            progress_change: SignalInstance,
            progress_text_change: SignalInstance,
            is_cancel_requested: Callable[[], bool],
        ):
            self.progress_change = progress_change
            self.progress_text_change = progress_text_change
            self.is_cancel_requested = is_cancel_requested

    class Status(IntEnum):
        NotStarted = 0
        Running = 1
        Finished = 2
        Canceled = 3

    class OperationCanceled(Exception):
        pass

    def __init__(self, target: Callable[[Promise.Data], T]):
        """
        Create a new promise
        :param target: The function to execute.
        """
        super().__init__()
        self._lock = Lock()
        self._status = self.Status.NotStarted
        self._cancel_requested = False
        self._target = target
        self._value: T = Void
        self._exception = Void

    ready = Signal()
    canceled = Signal()
    progress_change = Signal(float)
    progress_text_change = Signal(str)

    def _op_wrapper(self):
        try:
            value = self._target(
                Promise.Data(
                    self.progress_change,
                    self.progress_text_change,
                    self.is_cancel_requested,
                )
            )
        except self.OperationCanceled as e:
            self._exception = e
            self._status = self.Status.Canceled
            self.canceled.emit()
        except Exception as e:
            self._exception = e
            self._status = self.Status.Finished
            self.ready.emit()
        else:
            self._value = value
            self._status = self.Status.Finished
            self.ready.emit()

    def _thread_op_wrapper(self):
        enable_trace()
        self._op_wrapper()

    def _set_start(self):
        with self._lock:
            if self._status is not self.Status.NotStarted:
                raise RuntimeError("This promise has already been started.")
            self._status = self.Status.Running

    def start(self):
        """
        Run the operation wrapped by the promise in a new thread.
        This will return immediately.
        This can only be called once.
        """
        self._set_start()
        QThreadPool.globalInstance().start(self._thread_op_wrapper)

    def call(self) -> T:
        """
        Directly call the operation wrapped by the promise in this thread.
        Block until complete.
        Exceptions will be raised to the caller.
        This can only be called once.
        """
        self._set_start()
        self._op_wrapper()
        return self.get_return()

    def call_chained(
        self,
        parent_promise: Promise.Data,
        min_progress: float = 0.0,
        max_progress: float = 1.0,
    ) -> T:
        """
        Directly call the operation wrapped by this promise in this thread.
        Relay signals to another promise.
        Block until complete.
        This can only be called once.

        :param parent_promise: The parent promise to relay the signals to.
        :param min_progress: The minimum progress when relaying progress to the parent promise.
        :param max_progress: The maximum progress when relaying progress to the parent promise.
        :return:
        """
        self._set_start()

        progress_multiplier = max_progress - min_progress

        def tick(progress: float):
            parent_promise.progress_change.emit(
                progress * progress_multiplier + min_progress
            )
            if parent_promise.is_cancel_requested():
                self.cancel()

        self.progress_change.connect(tick)
        self.progress_text_change.connect(parent_promise.progress_text_change)

        self._op_wrapper()
        return self.get_return()

    def cancel(self):
        """
        Request the operation be canceled.
        It is down to the operation to implement support for this.
        """
        self._cancel_requested = True

    def is_cancel_requested(self) -> bool:
        """Has cancel been called to signal that the operation should be canceled."""
        return self._cancel_requested

    def status(self) -> Status:
        return self._status

    def get_return(self) -> T:
        """Get the return value or raise an exception if one occurred."""
        if self._value is not Void:
            return self._value
        elif self._exception is not Void:
            raise self._exception
        else:
            raise RuntimeError("The operation has not finished yet")
