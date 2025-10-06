from threading import Lock
from collections.abc import Callable

from PySide6.QtWidgets import QStyle, QStyleFactory, QApplication


class StyleStorage:
    def __init__(
        self, identifier: str, name: str, style_factory: Callable[[], QStyle] | str
    ):
        self.identifier = identifier
        self.name = name
        self.style_factory = style_factory


_lock = Lock()
_styles = dict[str, StyleStorage]()

PrettyStyleNames = {
    "windows11": "Windows 11",
    "windowsvista": "Windows Vista",
    "windows": "Windows (Legacy)",
    "fusion": "Fusion",
    "macos": "macOS",
    "android": "Android",
}

for style_key in QStyleFactory.keys():
    _styles[style_key] = StyleStorage(
        style_key, PrettyStyleNames.get(style_key, style_key), style_key
    )


def register_style(
    identifier: str, name: str, style_factory: Callable[[], QStyle]
) -> None:
    """
    Register a style.

    :param identifier: The unique identifier for the style. Eg "my_namespace.my_plugin.my_style"
    :param name: The human-readable name of the style. Eg "My Style"
    :param style_factory: A callable that returns an instance of your style.
        This can be the class object if it is default constructable.
    """
    with _lock:
        if identifier in _styles:
            raise RuntimeError(f"Style {identifier} has already been registered.")
        _styles[identifier] = StyleStorage(identifier, name, style_factory)


def unregister_style(identifier: str) -> None:
    """Remove the style"""
    with _lock:
        if identifier not in _styles:
            raise RuntimeError(f"Style {identifier} has not been registered.")
        del _styles[identifier]


def get_current_style_identifier() -> str:
    return QApplication.style().name()


def get_valid_styles() -> dict[str, str]:
    "Get a dictionary mapping valid style identifiers to style names."
    with _lock:
        return {identifier: storage.name for identifier, storage in _styles.items()}


def set_style(identifier: str) -> None:
    with _lock:
        storage = _styles[identifier]
        factory = _styles[identifier].style_factory
        if isinstance(factory, str):
            # Built in style
            style = QStyleFactory.create(factory)
        else:
            style = factory()
        QApplication.setStyle(style)
