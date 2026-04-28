from PySide6.QtCore import QObject, Signal

from amulet.app.localisation._app import init as init_localisation


class AppCreatedObject(QObject):
    app_created = Signal()


_obj = AppCreatedObject()
app_created = _obj.app_created

app_created.connect(init_localisation)
