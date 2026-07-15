import math
from collections.abc import Callable

from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QAbstractSpinBox

from amulet.nbt import ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag

Bounds = {
    ByteTag: (-(2**7), 2**7 - 1, int),
    ShortTag: (-(2**15), 2**15 - 1, int),
    IntTag: (-(2**31), 2**31 - 1, int),
    LongTag: (-(2**63), 2**63 - 1, int),
    FloatTag: (-math.inf, math.inf, float),
    DoubleTag: (-math.inf, math.inf, float),
}


class NBTSpinBox[TagT: ByteTag | ShortTag | IntTag | LongTag | FloatTag | DoubleTag](
    QAbstractSpinBox
):
    _minimum: int | float
    _maximum: int | float
    _py_cls: type[int | float]
    _cls: Callable[[int | float], TagT]

    def __init__(
        self: NBTSpinBox[TagT],
        value: TagT,
    ):
        super().__init__()
        self._cls = type(value)
        self._minimum, self._maximum, self._py_cls = Bounds[self._cls]
        self._value: TagT = value
        self._update_text()

    def value(self) -> TagT:
        return self._value

    def wrapping(self) -> bool:
        return True

    def _update_text(self) -> None:
        self.lineEdit().setText(str(self._value))

    def stepBy(self, steps: int) -> None:
        new_value = self._cls(self._value.py_data + steps)
        if new_value != self._value:
            self._value = new_value
            self._update_text()

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        return (
            QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
            | QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
        )

    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:
        text = text.strip()

        if text in ("", "+", "-"):
            return QValidator.State.Intermediate, text, pos

        try:
            py_value = self._py_cls(text)
        except ValueError:
            return QValidator.State.Invalid, text, pos

        if self._minimum <= py_value <= self._maximum:
            self._value = self._cls(py_value)
            return QValidator.State.Acceptable, text, pos

        return QValidator.State.Invalid, text, pos

    def fixup(self, text: str) -> str:
        try:
            py_value = self._py_cls(text)
        except ValueError:
            pass
        else:
            self._value = self._cls(py_value)
        return str(self._value)
