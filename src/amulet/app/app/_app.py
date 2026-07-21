from PySide6.QtWidgets import QApplication

from amulet.app.localisation._app import init as init_localisation


class AmuletApp(QApplication):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        init_localisation()
