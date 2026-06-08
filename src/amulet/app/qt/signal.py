"""Improved type hinting for Qt Signals."""

from __future__ import annotations

from typing import ParamSpec, Protocol, Any
from collections.abc import Sequence, Callable
from inspect import isclass

from PySide6.QtCore import Signal, Qt, QMetaObject

P = ParamSpec("P")


class TypeFormSignal:
    def __new__(
        cls, /, *types: Any, name: str = "", arguments: Sequence[str] = ()
    ) -> TypeFormSignal:
        return Signal(*(i if isclass(i) else object for i in types), name=name, arguments=arguments)  # type: ignore[return-value]


class SignalInstanceProtocol(Protocol[P]):
    def connect(
        self,
        slot: SignalInstanceProtocol[P] | Callable[P, Any],
        /,
        type: Qt.ConnectionType = Qt.ConnectionType.AutoConnection,
    ) -> QMetaObject.Connection: ...
    def disconnect(
        self, /, slot: SignalInstanceProtocol[P] | Callable[P, Any] | None = None
    ) -> bool: ...
    def emit(self, /, *args: P.args, **kwargs: P.kwargs) -> bool: ...
