from typing import Iterable, Union, Type

from PySide6.QtGui import QCloseEvent

from amulet_team_main_window._application.widget import Widget
from amulet_team_main_window._application.windows.window_proxy import (
    AbstractWindowProxy,
)
from .sub_window import Ui_AmuletSubWindow
from ..layout import Layout


class AmuletSubWindow(Ui_AmuletSubWindow):
    def closeEvent(self, event: QCloseEvent) -> None:
        # The parent keeps this object alive. We need to do this so it can be destroyed
        self.setParent(None)
        self.deleteLater()


class AmuletSubWindowProxy(AbstractWindowProxy):
    def set_layout(self, layout: Union[Type[Widget], Layout]) -> None:
        pass


# def get_sub_windows() -> Iterable[AmuletSubWindowProxy]:
#     return map(lambda window: window.proxy, AmuletSubWindowProxy.sub_windows())
