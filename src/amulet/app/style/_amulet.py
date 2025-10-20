from PySide6.QtWidgets import (
    QProxyStyle,
    QStyle,
    QStyleOption,
    QStyleOptionComplex,
    QStyleOptionButton,
    QStyleOptionComboBox,
    QWidget,
)
from PySide6.QtGui import QColor, QPainter


class AmuletStyle(QProxyStyle):
    def __init__(self) -> None:
        super().__init__("fusion")

    def drawControl(
        self,
        element: QStyle.ControlElement,
        option: QStyleOption,
        painter: QPainter,
        /,
        widget: QWidget | None = None,
    ) -> None:
        if element == QStyle.ControlElement.CE_PushButton and isinstance(
            option, QStyleOptionButton
        ):
            # Hover
            if option.state & QStyle.StateFlag.State_MouseOver:
                option.palette.setColor(
                    option.palette.ColorRole.Button, QColor("#919191")
                )

            # Checked state
            if option.state & QStyle.StateFlag.State_On:
                option.palette.setColor(
                    option.palette.ColorRole.Button, QColor("#4cc2ff")
                )
                option.palette.setColor(
                    option.palette.ColorRole.ButtonText, QColor("black")
                )

        super().drawControl(element, option, painter, widget)

    def drawComplexControl(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        painter: QPainter,
        /,
        widget: QWidget | None = None,
    ) -> None:
        if control == QStyle.ComplexControl.CC_ComboBox and isinstance(
            option, QStyleOptionComboBox
        ):
            if option.state & QStyle.StateFlag.State_MouseOver:
                option.palette.setColor(
                    option.palette.ColorRole.Button, QColor("#919191")
                )

        super().drawComplexControl(control, option, painter, widget)

    def name(self, /) -> str:
        return "amulet"
