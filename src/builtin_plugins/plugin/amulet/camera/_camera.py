from typing import NamedTuple, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QMatrix4x4


class Location(NamedTuple):
    x: float
    y: float
    z: float


class Rotation(NamedTuple):
    azimuth: float
    elevation: float


class Bounds(NamedTuple):
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float


class CameraExtrinsics(QObject):
    """
    A class to hold the camera extrinsic state.
    Note that this class is not thread safe.
    All operations must be called from the main thread.
    """

    # Signals
    # The matrix changed.
    transform_changed = Signal()
    # The camera moved
    location_changed = Signal()
    # The camera rotated
    rotation_changed = Signal()

    # Private variables
    _bounds: Bounds
    _speed: float
    # Extrinsic attrs
    _location: Location
    _rotation: Rotation
    # Matrix
    _matrix: Optional[QMatrix4x4]

    __slots__ = (
        "_bounds",
        "_speed",
        "_location",
        "_rotation",
        "_extrinsic_matrix",
    )

    def __init__(self, location: Location, rotation: Rotation) -> None:
        super().__init__()
        self._bounds = Bounds(
            -1_000_000_000,
            -1_000_000_000,
            -1_000_000_000,
            1_000_000_000,
            1_000_000_000,
            1_000_000_000,
        )
        self._speed = 1.0
        self._location = location
        self._rotation = rotation
        self._matrix = None

    def _clamp_location(self, location: Location) -> Location:
        return Location(
            min(max(self._bounds.min_x, location.x), self._bounds.max_x),
            min(max(self._bounds.min_y, location.y), self._bounds.max_y),
            min(max(self._bounds.min_z, location.z), self._bounds.max_z),
        )

    @property
    def speed(self) -> float:
        """The speed of the camera in blocks per second."""
        return self._speed

    @speed.setter
    def speed(self, speed: float) -> None:
        self._speed = speed

    @property
    def location(self) -> Location:
        """The location of the camera. (x, y, z)"""
        return self._location or Location(0.0, 0.0, 0.0)

    @location.setter
    def location(self, location: Location) -> None:
        """Set the location of the camera. (x, y, z)."""

        # Clamp location to the bounds.
        location = self._clamp_location(location)

        if location != self._location:
            self._location = location
            self._matrix = None
            self.location_changed.emit()
            self.transform_changed.emit()

    def _clamp_rotation(self, rotation: Rotation) -> Rotation:
        return Rotation(
            (
                rotation.azimuth
                if -180 <= rotation.azimuth < 180
                else ((rotation.azimuth + 180) % 360) - 180
            ),
            min(max(-90.0, rotation.elevation), 90.0),
        )

    @property
    def rotation(self) -> Rotation:
        """The rotation of the camera. (azimuth/yaw, elevation/pitch).
        This should behave the same as how Minecraft handles it.
        """
        return self._rotation or Rotation(0.0, 0.0)

    @rotation.setter
    def rotation(self, rotation: Rotation) -> None:
        """Set the rotation of the camera. (azimuth/yaw, elevation/pitch).
        azimuth (-180 to 180), elevation (-90 to 90)
        This should behave the same as how Minecraft handles it."""

        # Clamp rotation to the bounds
        rotation = self._clamp_rotation(rotation)

        if rotation != self._rotation:
            self._rotation = rotation
            self._matrix = None
            self.rotation_changed.emit()
            self.transform_changed.emit()

    def set_extrinsics(self, location: Location, rotation: Rotation) -> None:
        """Set the camera location and rotation at the same time."""
        location = self._clamp_location(location)
        rotation = self._clamp_rotation(rotation)
        location_changed = location != self._location
        rotation_changed = rotation != self._rotation

        if location_changed:
            self._location = location
        if rotation_changed:
            self._rotation = rotation

        if location_changed or rotation_changed:
            self._matrix = None

            if location_changed:
                self.location_changed.emit()

            if rotation_changed:
                self.rotation_changed.emit()

            self.transform_changed.emit()

    @property
    def matrix(self) -> QMatrix4x4:
        """The matrix storing all extrinsic parameters (location/rotation)"""
        if self._matrix is None:
            self._matrix = QMatrix4x4()
            location = self.location
            rotation = self.rotation
            self._matrix.rotate(rotation.elevation, 1, 0, 0)
            self._matrix.rotate(rotation.azimuth, 0, 1, 0)
            self._matrix.translate(-location.x, -location.y, -location.z)
        return self._matrix


_camera: CameraExtrinsics | None = None


def get_camera_extrinsics(
    default_location: Location, default_rotation: Rotation
) -> CameraExtrinsics:
    global _camera
    if _camera is None:
        _camera = CameraExtrinsics(default_location, default_rotation)
    return _camera
