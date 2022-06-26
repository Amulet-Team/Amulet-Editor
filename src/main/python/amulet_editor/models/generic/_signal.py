from inspect import isclass
from typing import Any, Callable, Optional


class Signal:
    def __init__(self, datatype: Optional[type] = Any) -> None:
        self._slots: set[Callable[..., None]] = set()
        self._datatype = datatype

    def connect(self, slot: Callable[..., None]) -> None:
        self._slots.add(slot)

    def disconnect(self, slot: Callable[..., None]) -> None:
        try:
            self._slots.remove(slot)
        except KeyError:
            pass

    def emit(self, data: Optional[Any] = None):
        if self._datatype is None and data is not None:
            raise TypeError("expected NoneType, {} found".format(type(data).__name__))
        elif data is not None and not (
            self._datatype is Any
            or isinstance(data, self._datatype)
            or (isclass(data) and issubclass(data, self._datatype))
        ):
            raise TypeError(
                "expected {}, {} found".format(
                    self._datatype.__name__, type(data).__name__
                )
            )

        if self._datatype is None:
            for slot in self._slots:
                slot()
        else:
            for slot in self._slots:
                slot(data)
