from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
)

from runtime_final import final


class TabButton(QPushButton):
    pass


class TabWidget(ABC):
    def __init__(self) -> None:
        self._tab = TabButton()
        self._tab.setCheckable(True)

    @staticmethod
    @abstractmethod
    def identifier() -> str:
        """
        The unique identifier for this tab widget class.
        Eg my_namespace.my_plugin.my_widget
        """
        raise NotImplementedError

    @final
    @property
    def tab(self) -> QPushButton:
        """
        The tab to display in the tab bar.
        You must set the text and may set an icon.
        Please keep other formatting to a minimum.
        """
        return self._tab

    @property
    @abstractmethod
    def widget(self) -> QWidget:
        """The widget associated with the tab."""
        raise NotImplementedError
