from __future__ import annotations

import json
import os
from typing import Any

import qtsass

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


class Color:
    def __init__(self, hex: str) -> None:
        self._qcolor = QColor(hex)

    def get_qcolor(self) -> QColor:
        return self._qcolor

    def get_hex(self) -> str:
        return self._qcolor.name()


def compile_qtsass(input_file: str, include_paths: list = None) -> str:
    input_root = os.path.abspath(os.path.dirname(input_file))
    include_paths = [input_root] + (include_paths or [])

    with open(input_file, 'r') as f:
        string = f.read()

    css = qtsass.compile(string, include_paths=include_paths)

    return css


class Theme:
    def __init__(self, theme_dir: str) -> None:

        with open(os.path.join(theme_dir, "theme.json"), "r") as fh:
            data: dict[str, Any] = json.load(fh)
        self._name = data["theme_name"]
        self._qss = compile_qtsass(os.path.join(theme_dir, "application.scss"))

    def apply(self, application: QApplication) -> None:
        """Apply theme to a `QtWidgets.QApplication`."""
        application.setStyleSheet(self._qss)

    @property
    def name(self) -> str:
        return self._name

    @property
    def primary_variant(self) -> Color:
        return Color("#808080")

    @property
    def on_primary(self) -> Color:
        return Color("#808080")

    @property
    def background(self) -> Color:
        return Color("#808080")

    @property
    def on_surface(self) -> Color:
        return Color("#808080")
