from PySide6.QtCore import QLocale, QObject, Signal, QTranslator, QCoreApplication


class LocaleObject(QObject):
    locale_changed = Signal(QLocale)


_obj = LocaleObject()
locale_changed = _obj.locale_changed


def set_locale(locale: QLocale):
    """Set the application locale"""
    QLocale.setDefault(locale)
    locale_changed.emit(locale)
    # Force a language change. The above should have only modified existing translators
    t = QTranslator()
    QCoreApplication.installTranslator(t)
    QCoreApplication.removeTranslator(t)
