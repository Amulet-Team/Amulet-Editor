"""Improved type hinting for Qt Signals."""

from __future__ import annotations

from typing import TypeVar, ParamSpec, Protocol, Any, overload
from collections.abc import Sequence, Callable
from typing_extensions import TypeForm  # TODO: move import to typing in 3.15

from PySide6.QtCore import Signal, Qt, QMetaObject

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
T7 = TypeVar("T7")
T8 = TypeVar("T8")
P = ParamSpec("P")
EmitT1 = ParamSpec("EmitT1")
EmitT2 = ParamSpec("EmitT2")
EmitT3 = ParamSpec("EmitT3")
EmitT4 = ParamSpec("EmitT4")
EmitT5 = ParamSpec("EmitT5")
EmitT6 = ParamSpec("EmitT6")
EmitT7 = ParamSpec("EmitT7")
EmitT8 = ParamSpec("EmitT8")
ArgsT1 = ParamSpec("ArgsT1")
ArgsT2 = ParamSpec("ArgsT2")
ArgsT3 = ParamSpec("ArgsT3")
ArgsT4 = ParamSpec("ArgsT4")
ArgsT5 = ParamSpec("ArgsT5")
ArgsT6 = ParamSpec("ArgsT6")
ArgsT7 = ParamSpec("ArgsT7")
ArgsT8 = ParamSpec("ArgsT8")

class TypeFormSignal(
    Signal[
        ArgsT1,
        ArgsT2,
        ArgsT3,
        ArgsT4,
        ArgsT5,
        ArgsT6,
        ArgsT7,
        ArgsT8,
        EmitT1,
        EmitT2,
        EmitT3,
        EmitT4,
        EmitT5,
        EmitT6,
        EmitT7,
        EmitT8,
    ]
):
    @overload
    def __init__(
        self: TypeFormSignal[
            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
        ],
        /,
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [],
            [],
            [],
            [],
            [],
            [],
            [T1],
            [T1],
            [T1],
            [T1],
            [T1],
            [T1],
            [T1],
            [T1],
        ],
        /,
        type_1: TypeForm[T1],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [],
            [],
            [],
            [],
            [],
            [T1, T2],
            [T1, T2],
            [T1, T2],
            [T1, T2],
            [T1, T2],
            [T1, T2],
            [T1, T2],
            [T1, T2],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [T1, T2, T3],
            [],
            [],
            [],
            [],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
            [T1, T2, T3],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        type_3: TypeForm[T3],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [T1, T2, T3],
            [T1, T2, T3, T4],
            [],
            [],
            [],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        type_3: TypeForm[T3],
        type_4: TypeForm[T4],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [T1, T2, T3],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4, T5],
            [],
            [],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        type_3: TypeForm[T3],
        type_4: TypeForm[T4],
        type_5: TypeForm[T5],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [T1, T2, T3],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5, T6],
            [],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        type_3: TypeForm[T3],
        type_4: TypeForm[T4],
        type_5: TypeForm[T5],
        type_6: TypeForm[T6],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self: TypeFormSignal[
            [],
            [T1],
            [T1, T2],
            [T1, T2, T3],
            [T1, T2, T3, T4],
            [T1, T2, T3, T4, T5],
            [T1, T2, T3, T4, T5, T6],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
            [T1, T2, T3, T4, T5, T6, T7],
        ],
        /,
        type_1: TypeForm[T1],
        type_2: TypeForm[T2],
        type_3: TypeForm[T3],
        type_4: TypeForm[T4],
        type_5: TypeForm[T5],
        type_6: TypeForm[T6],
        type_7: TypeForm[T7],
        *,
        name: str = "",
        arguments: Sequence[str] = (),
    ) -> None: ...
    @overload
    def __init__(
        self, /, *types: type, name: str = "", arguments: Sequence[str] = ()
    ) -> None: ...

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
