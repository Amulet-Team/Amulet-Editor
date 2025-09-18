"""A helper module to create singleton signals"""

from __future__ import annotations

from typing import Generic, TypeVar, TypeVarTuple, overload, Any
from collections.abc import Callable, Sequence
import inspect

from PySide6.QtCore import Signal as QSignal, Slot as QSlot, QObject, Qt, QMetaObject

T = TypeVar("T")
Ts = TypeVarTuple("Ts")


class SignalInstance(Generic[*Ts]):
    """
    A Qt SignalInstance class alias with improved type hinting.
    See :class:`Signal` for usage examples.
    """

    def connect(
        self,
        slot: QSignal | QSlot | Callable[[*Ts], None],
        /,
        type: Qt.ConnectionType = Qt.ConnectionType.AutoConnection,
    ) -> QMetaObject.Connection:
        raise RuntimeError("This should never be called")

    def disconnect(
        self, /, slot: QSignal | QSlot | Callable[[*Ts], None] | None = None
    ) -> bool:
        raise RuntimeError("This should never be called")

    def emit(self, /, *args: *Ts) -> None:
        raise RuntimeError("This should never be called")


class Signal(Generic[*Ts]):
    """
    A Qt Signal class alias with improved type hinting.

    >>> class MyClass(QObject):
    >>>     my_signal = Signal[int, float]()
    """

    _Ts: tuple[*Ts] | None = None

    def __new__(cls, name: str = "", arguments: Sequence[str] = ()) -> Signal:
        if cls._Ts is None:
            raise RuntimeError(
                "Signal must be specialised before it can be instantiated. Signal[int]()"
            )
        return QSignal(*(i if inspect.isclass(i) else type for i in cls._Ts), name=name, arguments=arguments)  # type: ignore

    @overload
    def __class_getitem__(cls, item: tuple[*Ts]) -> type[Signal[*Ts]]: ...
    @overload
    def __class_getitem__(cls, item: T) -> type[Signal[T]]: ...
    def __class_getitem__(
        cls, item: tuple[*Ts] | T
    ) -> type[Signal[*Ts]] | type[Signal[T]]:
        items = item if isinstance(item, tuple) else (item,)

        class SubSignal(Signal):
            _Ts = items

        return SubSignal

    @overload
    def __get__(self, instance: QObject, owner: Any, /) -> SignalInstance[*Ts]: ...
    @overload
    def __get__(self, instance: None, owner: Any, /) -> Signal[*Ts]: ...
    def __get__(
        self, instance: QObject | None, owner: Any, /
    ) -> Signal[*Ts] | SignalInstance[*Ts]:
        raise RuntimeError("This should never be called")


def create_signal(*args: *Ts) -> tuple[QObject, SignalInstance[*Ts]]:
    """
    Create a singleton signal.

    :param args: The argument types the signal will have
    :return: The QObject the signal is bound to and the signal instance
    """

    class ObjCls(QObject):
        signal = Signal[*args]()  # type: ignore

    obj = ObjCls()
    return obj, obj.signal
