from PySide6.QtCore import QObject, Signal


class RenderSettings(QObject):
    render_distance_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._chunk_load_distance = 5
        self._chunk_unload_distance = 100

    @property
    def chunk_load_distance(self) -> int:
        """The radius around the camera within which should be loaded."""
        return self._chunk_load_distance

    @property
    def chunk_unload_distance(self) -> int:
        """The radius around the camera outside which chunks should be unloaded."""
        return self._chunk_unload_distance

    def set_render_distance(self, load_distance: int, unload_distance: int) -> None:
        unload_distance = max(load_distance + 2, unload_distance)
        self._chunk_load_distance = load_distance
        self._chunk_unload_distance = unload_distance
        self.render_distance_changed.emit()

render_settings = RenderSettings()
