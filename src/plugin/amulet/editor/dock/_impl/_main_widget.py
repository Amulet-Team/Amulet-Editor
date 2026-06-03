from __future__ import annotations

import logging

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QShowEvent, QHideEvent

log = logging.getLogger(__name__)


class DockMainWidget(QWidget):
    def __init__(self, layout_name: str) -> None:
        super().__init__()
