from functools import cached_property

from amulet_editor.data import build
from amulet_editor.data.build import PUBLIC_DATA
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

if build.fbs_installed():
    from fbs_runtime.application_context.PySide6 import (
        ApplicationContext as BaseContext,
    )
else:

    class BaseContext:
        """Replacement import when running from source without fbs"""

        def __init__(self) -> None:
            self.app

            if self.app_icon is not None:
                self.app.setWindowIcon(self.app_icon)

        @cached_property
        def app(self):
            application = QApplication()
            application.setApplicationName(PUBLIC_DATA["app_name"])
            application.setApplicationVersion(PUBLIC_DATA["version"])
            return application

        @cached_property
        def app_icon(self):
            return QIcon(build.get_resource("Icon.ico"))

        def get_resource(self, rel_path: str):
            """This method should not be implemented.
            \nIt exists to immitate `ApplicationContext` from fbs."""
            raise NotImplementedError()

        def run(self):
            raise NotImplementedError()


class AmuletContext(BaseContext):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        from amulet_editor.application.context._amulet_app import AmuletEditor

        self._amulet_editor = AmuletEditor(self.app)
        return self._amulet_editor.app.exec()


AMULET_CONTEXT = AmuletContext()
