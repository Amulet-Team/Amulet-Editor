import os

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from amulet.app.localisation import Translator, locale_changed

_translator: Translator | None = None


def load_translations() -> None:
    global _translator

    if _translator is not None:
        return

    # Load the translations
    translator = _translator = Translator()

    def _load_translations() -> None:
        translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(os.path.dirname(__file__), "lang"),
        )

    _load_translations()
    QApplication.installTranslator(translator)
    locale_changed.connect(_load_translations)
