from typing import Optional, Union, TypeVar, Generic, Any, TYPE_CHECKING
import unittest

from PySide6.QtCore import QObject

from amulet.app.qt.signal import TypeFormSignal

T = TypeVar("T")


class MyGenericClass(Generic[T]):
    pass


class MyClass(QObject):
    signal_template_class = TypeFormSignal(MyGenericClass[int])
    signal_optional = TypeFormSignal(Optional[int])
    signal_union_1 = TypeFormSignal(Union[int, float])
    signal_union_2 = TypeFormSignal(int | float)
    signal_int = TypeFormSignal("int")


class NonTypeSignalTestCase(unittest.TestCase):
    def test_template_class(self) -> None:
        out: list[Any] = []
        c = MyClass()
        c.signal_template_class.connect(out.append)
        obj = MyGenericClass[int]()
        c.signal_template_class.emit(obj)
        self.assertEqual(out, [obj])
        if TYPE_CHECKING:
            c.signal_int.emit("test")  # type: ignore[call-overload]
            c.signal_int.emit(1.5)  # type: ignore[call-overload]
            c.signal_int.emit(None)  # type: ignore[call-overload]

    def test_optional(self) -> None:
        out: list[Any] = []
        c = MyClass()
        c.signal_optional.connect(out.append)
        c.signal_optional.emit(1)
        c.signal_optional.emit(None)
        self.assertEqual(out, [1, None])
        if TYPE_CHECKING:
            c.signal_int.emit("test")  # type: ignore[call-overload]

    def test_union_1(self) -> None:
        out: list[Any] = []
        c = MyClass()
        c.signal_union_1.connect(out.append)
        c.signal_union_1.emit(1)
        c.signal_union_1.emit(1.5)
        self.assertEqual(out, [1, 1.5])
        if TYPE_CHECKING:
            c.signal_int.emit("test")  # type: ignore[call-overload]
            c.signal_int.emit(None)  # type: ignore[call-overload]

    def test_union_2(self) -> None:
        out: list[Any] = []
        c = MyClass()
        c.signal_union_2.connect(out.append)
        c.signal_union_2.emit(1)
        c.signal_union_2.emit(1.5)
        self.assertEqual(out, [1, 1.5])
        if TYPE_CHECKING:
            c.signal_int.emit("test")  # type: ignore[call-overload]
            c.signal_int.emit(None)  # type: ignore[call-overload]

    def test_int(self) -> None:
        out: list[Any] = []
        c = MyClass()
        c.signal_int.connect(out.append)
        c.signal_int.emit(1)
        self.assertEqual(out, [1])
        if TYPE_CHECKING:
            c.signal_int.emit("test")  # type: ignore[call-overload]
            c.signal_int.emit(1.5)  # type: ignore[call-overload]
            c.signal_int.emit(None)  # type: ignore[call-overload]


if __name__ == "__main__":
    unittest.main()
