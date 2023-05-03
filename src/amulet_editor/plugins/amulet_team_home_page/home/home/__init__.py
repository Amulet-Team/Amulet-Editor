from amulet_editor import __version__

from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QImage, QPixmap
from amulet_editor.data import build
from ._home import Ui_HomePage


class HomePage(Ui_HomePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        amulet_logo = QPixmap(QImage(build.get_resource("images/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)
        self._lbl_app_icon.setPixmap(amulet_logo)
        self._lbl_app_version.setText(f"Version {__version__}")
        self._central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # TODO: work out why some character sets cannot be displayed

        default_locale = QLocale()
        locales: set[tuple[QLocale.Language, QLocale.Country]] = set()
        for language in QLocale.Language:
            if language in {QLocale.Language.AnyLanguage, QLocale.Language.C}:
                continue
            for territory in QLocale.countriesForLanguage(language):
                locale_key = (language, territory)
                # Filter out duplicates
                if locale_key in locales:
                    continue
                locales.add(locale_key)
                locale = QLocale(language, territory)
                native_language = (
                    locale.nativeLanguageName() or locale.languageToString(language)
                )
                native_territory = (
                    locale.nativeTerritoryName() or locale.territoryToString(territory)
                )

                if native_language and native_territory:
                    self.cbo_language.addItem(
                        f"{native_language} - {native_territory}", userData=locale
                    )
                    if (
                        default_locale.language() == language
                        and default_locale.territory() == territory
                    ):
                        self.cbo_language.setCurrentIndex(self.cbo_language.count() - 1)
