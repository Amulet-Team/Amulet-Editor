from abc import ABC, abstractmethod

from amulet_editor.models.package._view import AmuletView


class AmuletTool(ABC):
    @property
    @abstractmethod
    def page(self) -> AmuletView:
        """Returns a view object containing a widget which should be rendered as a page."""
        ...

    @property
    @abstractmethod
    def primary_panel(self) -> AmuletView:
        """Returns a view object containing a widget which should be rendered as a panel."""
        ...

    @property
    @abstractmethod
    def secondary_panel(self) -> AmuletView:
        """Returns a view object containing a widget which should be rendered as a panel."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this package."""
        ...

    @property
    @abstractmethod
    def icon_name(self) -> str:
        """Name of the svg icon used to represent this package."""
        ...
