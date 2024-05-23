from amulet_editor import __version__

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QImage, QPixmap
from amulet_editor.resources import get_resource
from ._home import Ui_HomePage


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


class HomePage(Ui_HomePage):
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget):
        super().__init__(parent, f)
        amulet_logo = QPixmap(QImage(get_resource("icons/amulet/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)
        self._lbl_app_icon.setPixmap(amulet_logo)
        self._lbl_app_version.setText(f"Version {__version__}")
        self._central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # TODO: work out why some character sets cannot be displayed
        locales, index = _get_locales()
        for text, locale in locales:
            self.cbo_language.addItem(text, userData=locale)
        self.cbo_language.setCurrentIndex(index)
