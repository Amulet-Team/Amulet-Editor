"""A helper module to create singleton signals"""

from typing import Any
from PySide6.QtCore import (
    Signal as _Signal,
    SignalInstance as _SignalInstance,
    QObject as _QObject,
)


def SingletonSignal(*args: Any) -> tuple[_QObject, _SignalInstance]:
    """
    Create a singleton signal.

    :param args: The argument types the signal will have
    :return: The QObject the signal is bound to and the signal instance
    """

    class ObjCls(_QObject):
        signal = _Signal(*args)

    obj = ObjCls()
    return obj, obj.signal
