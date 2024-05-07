from abc import ABC, abstractmethod
from typing import Union, Type

from amulet_team_main_window2._application.widget import Widget
from .layout import Layout


class AbstractWindowProxy(ABC):
    @abstractmethod
    def set_layout(self, layout: Union[Type[Widget], Layout]):
        """Configure the layout as requested"""
        raise NotImplementedError
