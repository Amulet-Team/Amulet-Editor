from inspect import isclass
from typing import Any, Callable, Optional


class Observer:
    def __init__(self, datatype: Optional[type] = Any):
        self._callbacks: set[Callable[..., None]] = set()
        self._datatype = datatype

    def connect(self, callback: Callable[..., None]):
        self._callbacks.add(callback)

    def disconnect(self, callback: Callable[..., None]):
        try:
            self._callbacks.remove(callback)
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
            for callback in self._callbacks:
                callback()
        else:
            for callback in self._callbacks:
                callback(data)
