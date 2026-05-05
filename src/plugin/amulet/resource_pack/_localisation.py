from amulet.app.app import app_created


def _init_localisation() -> None:
    import os
    from PySide6.QtCore import QLocale, QCoreApplication
    from amulet.app.localisation import Translator, locale_changed

    translator = Translator()

    def _locale_changed() -> None:
        from plugin.amulet.resource_pack import __path__ as resource_pack_path

        translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(*resource_pack_path, "lang"),
        )

    _locale_changed()
    QCoreApplication.installTranslator(translator)
    locale_changed.connect(_locale_changed)


app_created.connect(_init_localisation)
