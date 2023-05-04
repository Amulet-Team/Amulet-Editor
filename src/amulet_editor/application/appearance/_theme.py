from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from amulet_editor.data import build
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


class Color:
    def __init__(self, colour_hex: str):
        self._qcolor = QColor(colour_hex)

    def get_qcolor(self) -> QColor:
        return self._qcolor

    def get_hex(self) -> str:
        return self._qcolor.name()

    def get_rgb(self) -> str:
        return "rgb({}, {}, {})".format(*self._qcolor.getRgb())

    def get_rgba(self) -> str:
        return "rgba({}, {}, {}, {})".format(*self._qcolor.getRgb())

    def darker(self, percent: int = 100) -> Color:
        if percent < 0:
            raise ValueError("'percent' must be a positive integer")
        return Color(self._qcolor.darker(100 + percent).name())

    def lighter(self, percent: int = 50) -> Color:
        if percent < 0:
            raise ValueError("'percent' must be a positive integer")
        return Color(self._qcolor.lighter(100 + percent).name())


class Theme:
    def __init__(self, theme_dir: str):
        with open(os.path.join(theme_dir, "theme.json"), "r") as fh:
            self._theme: dict[str, Any] = json.load(fh)

        self._style_sheets: dict[str, str] = {}

        path_style_sheets = build.get_resource(
            os.path.join("themes", "_default", "style_sheets")
        )
        for style_name in os.listdir(path_style_sheets):
            self._style_sheets[style_name] = self.load_style_sheet(
                os.path.join(path_style_sheets, style_name)
            )

        path_style_sheets = os.path.join(theme_dir, "style_sheets")
        if os.path.isdir(path_style_sheets):
            for style_name in os.listdir(path_style_sheets):
                self._style_sheets[style_name] = self.load_style_sheet(
                    os.path.join(path_style_sheets, style_name)
                )

    def apply(self, application: QApplication):
        """Apply theme to a `QtWidgets.QApplication`."""
        application.setStyle(self._theme["style"])
        application.setStyleSheet(self._style_sheets["application.qss"])

    def get_style_sheet(self, file_name: str) -> str:
        """Returns Qt style sheet from current theme with matching file name."""
        return self._style_sheets.get(file_name, "")

    def load_style_sheet(self, file_path: str) -> str:
        """Returns Qt style sheet at the provided file path. Substitutes placeholder colors with theme colors.
        \nGenerally `get_style_sheet()` should be used instead of this method.
        """
        with open(file_path, "r") as fh:
            style_sheet = fh.read().replace('"', "")

        icons: set[str] = set(
            [icon for icon in re.findall("url\((.*?)\)", style_sheet)]
        )
        for icon in icons:
            style_sheet = style_sheet.replace(
                "url({})".format(icon),
                "url({})".format(
                    Path(build.get_resource(os.path.join("icons", icon))).as_posix()
                ),
            )

        font_subfamilies: set[str] = set(
            [
                subfamily
                for subfamily in re.findall("{(.+?)}", style_sheet)
                if "font_family." in subfamily
            ]
        )
        for subfamily in font_subfamilies:
            try:
                font_data = subfamily.split(".")
                style_sheet = style_sheet.replace(
                    f"{{{subfamily}}}",
                    '"{}"'.format(
                        " ".join(
                            [
                                self.font_family,
                                self.font_subfamilies.get(font_data[1], ""),
                            ]
                        ).strip()
                    ),
                )
            except:
                raise ValueError(
                    f'unparsable font data: "{font_data}" in stylesheet "{file_path}"'
                )

        modified_colors: set[str] = set(
            [
                color
                for color in re.findall("{(.+?)}", style_sheet)
                if color not in self._theme["material_colors"]
                and color.rsplit(".", 2)[0] in self._theme["material_colors"]
            ]
        )
        for modified_color in modified_colors:
            try:
                color_data = modified_color.split(".")
                if color_data[1] == "darker":
                    style_sheet = style_sheet.replace(
                        f"{{{modified_color}}}",
                        Color(self._theme["material_colors"][color_data[0]])
                        .darker(int(color_data[2]))
                        .get_hex(),
                    )
                elif color_data[1] == "lighter":
                    style_sheet = style_sheet.replace(
                        f"{{{modified_color}}}",
                        Color(self._theme["material_colors"][color_data[0]])
                        .lighter(int(color_data[2]))
                        .get_hex(),
                    )
            except:
                raise ValueError(
                    f'unparsable color data: "{color_data}" in stylesheet "{file_path}"'
                )

        return style_sheet.format(
            font_family=self.font_family,
            background=self.background.get_hex(),
            error=self.error.get_hex(),
            primary=self.primary.get_hex(),
            primary_variant=self.primary_variant.get_hex(),
            secondary=self.secondary.get_hex(),
            secondary_variant=self.secondary_variant.get_hex(),
            surface=self.surface.get_hex(),
            on_background=self.on_background.get_hex(),
            on_error=self.on_error.get_hex(),
            on_primary=self.on_primary.get_hex(),
            on_secondary=self.on_secondary.get_hex(),
            on_surface=self.on_surface.get_hex(),
        )

    @property
    def name(self) -> str:
        return self._theme["theme_name"]

    @property
    def font_family(self) -> str:
        return self._theme["font"]["family"]

    @property
    def font_subfamilies(self) -> dict[str, str]:
        return self._theme["font"].get("subfamilies", {})

    @property
    def font_size(self) -> str:
        return self._theme["font"]["size"]

    @property
    def primary(self) -> Color:
        return Color(self._theme["material_colors"]["primary"])

    @property
    def primary_variant(self) -> Color:
        return Color(self._theme["material_colors"]["primary_variant"])

    @property
    def on_primary(self) -> Color:
        return Color(self._theme["material_colors"]["on_primary"])

    @property
    def secondary(self) -> Color:
        return Color(self._theme["material_colors"]["secondary"])

    @property
    def secondary_variant(self) -> Color:
        return Color(self._theme["material_colors"]["secondary_variant"])

    @property
    def on_secondary(self) -> Color:
        return Color(self._theme["material_colors"]["on_secondary"])

    @property
    def background(self) -> Color:
        return Color(self._theme["material_colors"]["background"])

    @property
    def on_background(self) -> Color:
        return Color(self._theme["material_colors"]["on_background"])

    @property
    def surface(self) -> Color:
        return Color(self._theme["material_colors"]["surface"])

    @property
    def on_surface(self) -> Color:
        return Color(self._theme["material_colors"]["on_surface"])

    @property
    def error(self) -> Color:
        return Color(self._theme["material_colors"]["error"])

    @property
    def on_error(self) -> Color:
        return Color(self._theme["material_colors"]["on_error"])
