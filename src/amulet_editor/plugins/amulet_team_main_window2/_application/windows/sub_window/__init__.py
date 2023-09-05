from typing import Iterable, Union, Type

from amulet_team_main_window2._application.widget import Widget
from amulet_team_main_window2._application.windows.window_proxy import (
    AbstractWindowProxy,
)
from .sub_window import Ui_AmuletSubWindow
from ..layout import Layout


class AmuletSubWindow(Ui_AmuletSubWindow):
    pass


class AmuletSubWindowProxy(AbstractWindowProxy):
    def set_layout(self, layout: Union[Type[Widget], Layout]):
        pass


# def get_sub_windows() -> Iterable[AmuletSubWindowProxy]:
#     return map(lambda window: window.proxy, AmuletSubWindowProxy.sub_windows())
