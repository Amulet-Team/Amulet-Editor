from typing import Union, Callable, Optional, Literal
from threading import Lock
from enum import IntEnum

from PySide6.QtCore import QObject, QEvent, Slot, Signal, QTimer, Qt
from PySide6.QtGui import QMouseEvent, QKeyEvent


"""
When a key is released, we stop all all events that need that key.
When a key is pressed, we find all events bound to that trigger key with satisfied modifier keys (if any).
    If none of new events have modifier keys, add them to the stack.
    If any of the events have modifier keys cancel all running events and take one event with the most modifier keys and run it.
"""


class KeySrc(IntEnum):
    Mouse = 1
    Keyboard = 2


KeyT = Union[
    tuple[Literal[KeySrc.Mouse], Qt.MouseButton], tuple[Literal[KeySrc.Keyboard], int]
]
ModifierT = frozenset[KeyT]
Number = Union[float, int]
ReceiverT = Union[Slot, Signal, Callable[[], None]]


class TimerData:
    receivers: set[ReceiverT]
    timer: QTimer

    def __init__(self, timer: QTimer = None):
        self.receivers = set()
        self.timer = timer or QTimer()


class EventStorage(QObject):
    one_shot = Signal()

    def __init__(self, key: KeyT, modifiers: frozenset[KeyT]):
        super().__init__()
        self.key = key
        self.modifiers = modifiers
        # Map from timer interval to bound methods and timers
        self.timers: dict[Number, TimerData] = {}
        # Weak pointers to the bound objects
        self.bound_one_shot: set = set()


class KeyCatcher(QObject):
    """
    A class to catch key presses in a widget and generate events in a more useful format.
    >>> from PySide6.QtWidgets import QWidget
    >>> widget = QWidget()
    >>> key_catcher = KeyCatcher()
    >>> widget.installEventFilter(key_catcher)
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._lock = Lock()
        self._pressed_buttons: set[KeyT] = set()
        # Mapping from the trigger key and modifier keys to the storages. 1:1
        self._key_combos: dict[KeyT, dict[ModifierT, EventStorage]] = {}
        # Mapping from all involved keys to the storages. Many:1
        self._keys: dict[KeyT, list[EventStorage]] = {}

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and isinstance(
            event, QMouseEvent
        ):
            self._key_pressed((KeySrc.Mouse, event.button()))
        elif event.type() == QEvent.Type.MouseButtonRelease and isinstance(
            event, QMouseEvent
        ):
            self._key_released((KeySrc.Mouse, event.button()))
        elif event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            if not event.isAutoRepeat():
                self._key_pressed((KeySrc.Keyboard, event.key()))
        elif event.type() == QEvent.Type.KeyRelease and isinstance(event, QKeyEvent):
            if not event.isAutoRepeat():
                self._key_released((KeySrc.Keyboard, event.key()))
        return super().eventFilter(watched, event)

    def _key_pressed(self, key: KeyT):
        print("pressed", key)
        with self._lock:
            if key not in self._pressed_buttons:
                self._pressed_buttons.add(key)
                # Find the storage with the most matching modifiers
                best_storage: Optional[EventStorage] = None
                for storage in self._key_combos.get(key, {}).values():
                    if storage.modifiers.issubset(self._pressed_buttons) and (
                        best_storage is None
                        or len(storage.modifiers) > len(best_storage.modifiers)
                    ):
                        best_storage = storage

                timer_data: TimerData
                if best_storage is not None:
                    if best_storage.modifiers:
                        # If a key with modifiers was pressed stop all the other timers.
                        for storage_dict in self._key_combos.values():
                            for storage in storage_dict.values():
                                for timer_data in storage.timers.values():
                                    timer_data.timer.stop()
                    for interval, timer_data in list(best_storage.timers.items()):
                        if timer_data.receivers:
                            timer_data.timer.timeout.emit()
                            timer_data.timer.start()
                        else:
                            del best_storage.timers[interval]
                    best_storage.one_shot.emit()

    def _key_released(self, key: KeyT):
        print("released", key)
        with self._lock:
            for storage in self._keys.get(key, ()):
                for timer_data in storage.timers.values():
                    timer_data.timer.stop()
            self._pressed_buttons.remove(key)

    def _get_storage(self, key: KeyT, modifiers: frozenset[KeyT]):
        """Lock must be acquired when calling this"""
        key_storage = self._key_combos.setdefault(key, {})
        if modifiers not in key_storage:
            storage = EventStorage(key, modifiers)
            key_storage[modifiers] = storage
            for key_ in (key, *modifiers):
                self._keys.setdefault(key_, []).append(storage)
        return key_storage[modifiers]

    def _clean_storage(self, key: KeyT, modifiers: frozenset[KeyT]):
        """Lock must be acquired when calling this"""
        # Get the storage
        storage = self._get_storage(key, modifiers)
        # Remove all unused timers.
        for interval in list(storage.timers.keys()):
            if not storage.timers[interval].receivers:
                del storage.timers[interval]
        # Remove storage if there are no bound receivers
        if not storage.bound_one_shot and not storage.timers:
            del self._key_combos[key][modifiers]
        # Remove trigger key if no storages
        if not self._key_combos[key]:
            del self._key_combos[key]

    def connect_single_shot(
        self,
        receiver: Union[Slot, Signal, Callable[[], None]],
        key: KeyT,
        modifiers: frozenset[KeyT],
    ):
        """
        Connect a receiver (slot, signal or function) to a key press that is called once when pressed.

        :param receiver: The slot, signal or callable that is notified when the key combination is pressed.
        :param key: The
        :param modifiers:
        :return:
        """
        with self._lock:
            storage = self._get_storage(key, modifiers)
            storage.bound_one_shot.add(receiver)
            storage.one_shot.connect(receiver)

    def disconnect_single_shot(
        self,
        receiver: Union[Slot, Signal, Callable[[], None]],
        key: KeyT,
        modifiers: frozenset[KeyT],
    ):
        with self._lock:
            storage = self._get_storage(key, modifiers)
            if receiver in storage.bound_one_shot:
                storage.one_shot.disconnect(receiver)
                storage.bound_one_shot.remove(receiver)
            self._clean_storage(key, modifiers)

    def connect_repeating(
        self,
        receiver: Union[Slot, Signal, Callable[[], None]],
        key: KeyT,
        modifiers: frozenset[KeyT],
        interval: int,
    ):
        """"""
        with self._lock:
            storage = self._get_storage(key, modifiers)
            if interval not in storage.timers:
                timer = QTimer()
                timer.setInterval(interval)
                storage.timers[interval] = TimerData(timer)
            timer_data = storage.timers[interval]
            timer_data.timer.timeout.connect(receiver)
            timer_data.receivers.add(receiver)

    def disconnect_repeating(
        self,
        receiver: Union[Slot, Signal, Callable[[], None]],
        key: KeyT,
        modifiers: frozenset[KeyT],
        interval: int,
    ):
        with self._lock:
            storage = self._get_storage(key, modifiers)
            timer_data = storage.timers.get(interval)
            if timer_data is not None:
                timer_data.timer.timeout.disconnect(receiver)
                timer_data.receivers.remove(receiver)
            self._clean_storage(key, modifiers)


def _demo():
    from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout

    app = QApplication()
    window = QWidget()

    grid = QGridLayout(window)
    grid.addWidget(QLabel("a 100ms"), 0, 0)
    grid.addWidget(QLabel("b 1000ms"), 1, 0)
    grid.addWidget(QLabel("c one shot"), 2, 0)
    label_a = QLabel("0")
    label_b = QLabel("0")
    label_c = QLabel("0")
    grid.addWidget(label_a, 0, 1)
    grid.addWidget(label_b, 1, 1)
    grid.addWidget(label_c, 2, 1)

    a = 0
    b = 0
    c = 0

    def update_a():
        nonlocal a
        a += 1
        label_a.setText(str(a))

    def update_b():
        nonlocal b
        b += 1
        label_b.setText(str(b))

    def update_c():
        nonlocal c
        c += 1
        label_c.setText(str(c))

    key_catcher = KeyCatcher()
    key_catcher.connect_repeating(
        update_a, (KeySrc.Keyboard, Qt.Key.Key_A), frozenset(), 100
    )
    key_catcher.connect_repeating(
        update_b, (KeySrc.Keyboard, Qt.Key.Key_B), frozenset(), 1000
    )
    key_catcher.connect_single_shot(
        update_c, (KeySrc.Keyboard, Qt.Key.Key_C), frozenset()
    )

    window.installEventFilter(key_catcher)

    window.show()
    window.setFocus()
    app.exec()


if __name__ == "__main__":
    _demo()