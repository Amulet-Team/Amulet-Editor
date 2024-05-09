from abc import ABC, abstractmethod
from typing import Union, Type

from amulet_team_main_window._application.widget import Widget
from .layout import Layout


class AbstractWindowProxy(ABC):
    @abstractmethod
    def set_layout(self, layout: Union[Type[Widget], Layout]) -> None:
        """Configure the layout as requested"""
        raise NotImplementedError
