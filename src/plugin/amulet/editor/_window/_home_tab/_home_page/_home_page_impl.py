from amulet.app import __version__

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QImage, QPixmap

from amulet.app.resource import get_resource_path
from amulet.app.localisation import set_locale
from amulet.app.style import get_current_style_identifier, get_valid_styles, set_style

from ._home_page_gui import HomePageGUI

_locales: tuple[tuple[tuple[str, QLocale], ...], int] | None = None


def _get_locales() -> tuple[tuple[tuple[str, QLocale], ...], int]:
    global _locales
    if _locales is None:
        default_locale = QLocale()
        locales_set = set[tuple[QLocale.Language, QLocale.Country]]()
        locales = list[tuple[str, QLocale]]()
        native_locale: int = 0
        for language in QLocale.Language:
            if language in {QLocale.Language.AnyLanguage, QLocale.Language.C}:
                continue
            for territory in QLocale.countriesForLanguage(language):
                locale_key = (language, territory)
                # Filter out duplicates
                if locale_key in locales_set:
                    continue
                locales_set.add(locale_key)
                locale = QLocale(language, territory)
                native_language = (
                    locale.nativeLanguageName() or locale.languageToString(language)
                )
                native_territory = (
                    locale.nativeTerritoryName() or locale.territoryToString(territory)
                )

                if native_language and native_territory:
                    locales.append((f"{native_language} - {native_territory}", locale))
                    if (
                        default_locale.language() == language
                        and default_locale.territory() == territory
                    ):
                        native_locale = len(locales) - 1
        _locales = tuple(locales), native_locale
    return _locales


class HomePage(HomePageGUI):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        amulet_logo = QPixmap(QImage(get_resource_path("icons/amulet/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)
        self._lbl_app_icon.setPixmap(amulet_logo)
        self._lbl_app_version.setText(f"Version {__version__}")
        self._central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # TODO: work out why some character sets cannot be displayed
        locales, index = _get_locales()
        for text, locale in locales:
            self._language.addItem(text, userData=locale)
        self._language.setCurrentIndex(index)
        self._language.currentIndexChanged.connect(self._language_changed)

        # Get the valid styles sorted alphabetically by name.
        def alphasort(key: tuple[str, str]) -> tuple[str, str]:
            return key[1].lower(), key[1].swapcase()

        styles = sorted(get_valid_styles().items(), key=alphasort)

        active_style = get_current_style_identifier()
        index = 0
        for i, (style_id, style_name) in enumerate(styles):
            self._style.addItem(style_name, userData=style_id)
            if style_id == active_style:
                index = i
        self._style.currentIndexChanged.connect(self._style_changed)
        self._style.setCurrentIndex(index)

        self._colour_scheme.clicked.connect(self._colour_scheme_changed)
        self._colour_scheme.setChecked(
            QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        )
        self._set_colour_scheme_label()

    def _language_changed(self) -> None:
        set_locale(self._language.currentData())

    def _style_changed(self) -> None:
        style = self._style.currentData()
        if style != get_current_style_identifier():
            set_style(style)

    def _colour_scheme_changed(self, is_dark: bool) -> None:
        self._set_colour_scheme_label()
        scheme = Qt.ColorScheme.Dark if is_dark else Qt.ColorScheme.Light
        hints = QApplication.styleHints()
        if scheme != hints.colorScheme():
            hints.setColorScheme(scheme)

    def _set_colour_scheme_label(self) -> None:
        self._colour_scheme.setText(
            QApplication.translate(
                "plugin.amulet.editor.HomePage",
                "dark_mode" if self._colour_scheme.isChecked() else "light_mode",
                None,
            )
        )

    def _localise(self) -> None:
        super()._localise()
        self._set_colour_scheme_label()
