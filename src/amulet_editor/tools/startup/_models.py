import enum
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Protocol, TypeVar

from amulet_editor.models.generic import Observer
from PySide6.QtWidgets import QWidget

SelfMenu = TypeVar("SelfMenu", bound="Menu")


class AutoName(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


class Navigate(AutoName):
    BACK = enum.auto()
    HERE = enum.auto()
    NEXT = enum.auto()


@dataclass
class ProjectData:
    name: str
    directory: str
    level_directory: Optional[str] = None


class Menu(Protocol):
    @abstractmethod
    def __init__(self, set_panel: Callable):
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        """Text to dispaly in menu header."""
        raise NotImplementedError

    @property
    @abstractmethod
    def enable_next(self) -> Observer:
        """Observer used by the menu handler to enable the next/finish button."""
        raise NotImplementedError

    @abstractmethod
    def navigated(self, destination):
        """Receives a Navigate enum to convey navigation to and from this menu."""
        raise NotImplementedError

    @abstractmethod
    def widget(self) -> QWidget:
        """Returns a widget containing all menu components."""
        raise NotImplementedError

    @abstractmethod
    def next_menu(self) -> Optional[SelfMenu]:
        """Returns the next Menu to display."""
        raise NotImplementedError
