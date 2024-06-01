from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, TypeVar
from abc import ABC, abstractmethod

from amulet_editor.resources import get_resource
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

T = TypeVar("T")


def dynamic_cast(obj: Any, cls: type[T]) -> T:
    if isinstance(obj, cls):
        return obj
    raise TypeError(f"{obj} is not an instance of {cls}")


class Color:
    def __init__(self, colour_hex: str):
        self._qcolor = QColor(colour_hex)

    def get_hex(self) -> str:
        return self._qcolor.name()

    def darker(self, percent: int = 100) -> Color:
        if percent < 0:
            raise ValueError("'percent' must be a positive integer")
        return Color(self._qcolor.darker(100 + percent).name())

    def lighter(self, percent: int = 50) -> Color:
        if percent < 0:
            raise ValueError("'percent' must be a positive integer")
        return Color(self._qcolor.lighter(100 + percent).name())


class AbstractBaseTheme(ABC):
    @abstractmethod
    def apply(self, application: QApplication) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class LegacyTheme(AbstractBaseTheme):
    def __init__(self, theme_dir: str):
        with open(os.path.join(theme_dir, "theme.json"), "r") as fh:
            theme_json: dict = dynamic_cast(json.load(fh), dict)

        self._name: str = dynamic_cast(theme_json["theme_name"], str)

        # Get the style theme
        self._style: str = dynamic_cast(theme_json["style"], str)

        style_sheet_path = os.path.join(theme_dir, "style_sheets", "application.qss")
        if not os.path.isfile(style_sheet_path):
            # If no override is defined fall back to the default.
            style_sheet_path = get_resource(
                os.path.join("themes", "_default", "style_sheets", "application.qss")
            )

        # Load the style sheet
        with open(style_sheet_path) as f:
            raw_style_sheet = f.read()

        # Format the style sheet.
        self._style_sheet = self._format_style_sheet(raw_style_sheet, theme_json)

    @staticmethod
    def _format_style_sheet(raw_style_sheet: str, theme_json: dict[str, Any]) -> str:
        """Returns Qt style sheet. Substitutes placeholder colors with theme colors."""
        style_sheet = raw_style_sheet.replace('"', "")

        font_family = theme_json["font"]["family"]
        font_subfamilies = theme_json["font"].get("subfamilies", {})
        primary = Color(theme_json["material_colors"]["primary"])
        primary_variant = Color(theme_json["material_colors"]["primary_variant"])
        on_primary = Color(theme_json["material_colors"]["on_primary"])
        secondary = Color(theme_json["material_colors"]["secondary"])
        secondary_variant = Color(theme_json["material_colors"]["secondary_variant"])
        on_secondary = Color(theme_json["material_colors"]["on_secondary"])
        background = Color(theme_json["material_colors"]["background"])
        on_background = Color(theme_json["material_colors"]["on_background"])
        surface = Color(theme_json["material_colors"]["surface"])
        on_surface = Color(theme_json["material_colors"]["on_surface"])
        error = Color(theme_json["material_colors"]["error"])
        on_error = Color(theme_json["material_colors"]["on_error"])

        icons: set[str] = set(
            [icon for icon in re.findall(r"url\((.*?)\)", style_sheet)]
        )
        for icon in icons:
            style_sheet = style_sheet.replace(
                "url({})".format(icon),
                "url({})".format(
                    Path(get_resource(os.path.join("icons", icon))).as_posix()
                ),
            )

        font_subfamilies_: set[str] = set(
            [
                subfamily
                for subfamily in re.findall("{(.+?)}", style_sheet)
                if "font_family." in subfamily
            ]
        )
        for subfamily in font_subfamilies_:
            font_data = subfamily.split(".")
            style_sheet = style_sheet.replace(
                f"{{{subfamily}}}",
                '"{}"'.format(
                    " ".join(
                        [
                            font_family,
                            font_subfamilies.get(font_data[1], ""),
                        ]
                    ).strip()
                ),
            )

        modified_colors: set[str] = set(
            [
                color
                for color in re.findall("{(.+?)}", style_sheet)
                if color not in theme_json["material_colors"]
                and color.rsplit(".", 2)[0] in theme_json["material_colors"]
            ]
        )
        for modified_color in modified_colors:
            color_data = modified_color.split(".")
            if color_data[1] == "darker":
                style_sheet = style_sheet.replace(
                    f"{{{modified_color}}}",
                    Color(theme_json["material_colors"][color_data[0]])
                    .darker(int(color_data[2]))
                    .get_hex(),
                )
            elif color_data[1] == "lighter":
                style_sheet = style_sheet.replace(
                    f"{{{modified_color}}}",
                    Color(theme_json["material_colors"][color_data[0]])
                    .lighter(int(color_data[2]))
                    .get_hex(),
                )

        return style_sheet.format(
            font_family=font_family,
            background=background.get_hex(),
            error=error.get_hex(),
            primary=primary.get_hex(),
            primary_variant=primary_variant.get_hex(),
            secondary=secondary.get_hex(),
            secondary_variant=secondary_variant.get_hex(),
            surface=surface.get_hex(),
            on_background=on_background.get_hex(),
            on_error=on_error.get_hex(),
            on_primary=on_primary.get_hex(),
            on_secondary=on_secondary.get_hex(),
            on_surface=on_surface.get_hex(),
        )

    def apply(self, application: QApplication) -> None:
        application.setStyle(self._style)
        application.setStyleSheet(self._style_sheet)

    @property
    def name(self) -> str:
        return self._name
