from __future__ import annotations
from typing import Optional, Type, TypeVar, Callable
from PySide6.QtCore import Slot, Signal, QObject, QThread, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget
import sys
from time import sleep
from threading import Thread, get_ident
from weakref import WeakSet

from runtime_final import final

_plugins = {}


def hide_instance():
    raise RuntimeError("You cannot access the app instance.")


QGuiApplication.instance = hide_instance


T = TypeVar("T")


@final
class InvokeMethod(QObject):
    def __init__(self):
        """
        Invokes a method on the main thread. Taking care of garbage collection "bugs".
        """
        super().__init__()
        self.__method = None
        self.__return = None

    @classmethod
    def invoke(cls, app: QApplication, method: Callable[[], T]) -> T:
        """
        Invoke a method in the main thread and optionally get the return value in a callback.

        :param app: The instance of the QApplication
        :param method: The method to be called in the main thread.
        :return: The method return value.
        """
        self = cls()
        self.__method = method
        self.__return = None
        self.start_signal.connect(self.execute, Qt.DirectConnection if app.thread() is self.thread() else Qt.BlockingQueuedConnection)
        # Move to the application thread
        self.moveToThread(app.thread())
        self.setParent(app)
        # Connect slots and start execute

        self.start_signal.emit()
        self.setParent(None)
        return self.__return

    start_signal = Signal()

    @Slot()
    def execute(self):
        self.__return = self.__method()


# class QThread2(QThread):
#     def __init__(self, parent: QObject = None, target=None, args=(), kwargs=()):
#         super().__init__(parent)
#         self.__target = target
#         self.__args = args
#         self.__kwargs = dict(kwargs)
#
#     def run(self):
#         self.__target(*self.__args, **self.__kwargs)


class Plugin:
    def run(self):
        raise NotImplementedError


PluginT = TypeVar("PluginT", bound=Plugin)
QObjectT = TypeVar("QObjectT", bound=QObject)


def load_plugin(plugin_cls: Type[Plugin]):
    plugin = plugin_cls()
    _plugins[plugin_cls] = plugin
    plugin.run()


def get_plugin(plugin_cls: Type[PluginT]) -> PluginT:
    return _plugins[plugin_cls]


class AppPlugin(Plugin):
    __app: Optional[QApplication]
    __thread: Optional[Thread]
    __objects: WeakSet[QObject]

    def __init__(self):
        self.__app = None
        self.__thread = None
        self.__objects = WeakSet()

    def run(self):
        self.__thread = Thread(target=self._thread)
        self.__thread.start()
        while self.__app is None:
            sleep(0.01)

    def _thread(self):
        print("app thread", get_ident())
        self.__app = QApplication()
        window = self.create_qobject(QWidget)
        window.show()
        sys.exit(self.__app.exec())

    def create_qobject(self, qobject_cls: Type[QObjectT], *args, **kwargs, ) -> QObjectT:
        """
        Create a new QObject or QWidget.
        """
        if not issubclass(qobject_cls, QObject):
            raise TypeError("qobject_cls must be a subclass of QObject")
        obj = InvokeMethod.invoke(self.__app, lambda: qobject_cls(*args, **kwargs))
        self.__objects.add(obj)
        return obj

    def call_in_gui_thread(self, func, *args, **kwargs):
        return InvokeMethod.invoke(self.__app, lambda: func(*args, **kwargs))


class Plugin2(Plugin):
    def __init__(self):
        self.__window = None

    def run(self):
        app_plugin = get_plugin(AppPlugin)
        self.__window = app_plugin.create_qobject(QWidget)
        app_plugin.call_in_gui_thread(self.__window.show)


def main():
    print("main thread", get_ident())
    load_plugin(AppPlugin)
    load_plugin(Plugin2)


if __name__ == '__main__':
    main()
