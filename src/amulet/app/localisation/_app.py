import os

from amulet.app.localisation import Translator, locale_changed

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

_translator = Translator()


def get_lang_directory() -> str:
    return os.path.join(os.path.dirname(__file__), "lang")


def load_translations() -> None:
    _translator.load_lang(QLocale(), "", directory=get_lang_directory())


def init() -> None:
    """
    Initialise application localisation.
    This must be called soon after initialising QApplication.
    """
    load_translations()
    QApplication.installTranslator(_translator)
    locale_changed.connect(load_translations)
