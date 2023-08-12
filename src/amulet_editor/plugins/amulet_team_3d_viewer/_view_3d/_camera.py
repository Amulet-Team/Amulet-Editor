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


class Camera(QObject):
    """A class to hold the state information of the camera."""

    # Signals
    # The intrinsic or extrinsic matrix changed.
    transform_changed = Signal()
    # Camera internal state (FOV/aspect/projection/clipping) changed.
    intrinsics_changed = Signal()
    # Camera external state (location/rotation) changed.
    extrinsics_changed = Signal()
    # The camera moved
    location_changed = Signal()
    # The camera rotated
    rotation_changed = Signal()

    # Private variables
    _bounds: Bounds
    # Extrinsic attrs
    _location: Location
    _rotation: Rotation
    # Matrix
    _intrinsic_matrix: QMatrix4x4
    _extrinsic_matrix: Optional[QMatrix4x4]

    __slots__ = (
        "_bounds",
        "_location",
        "_rotation",
        "_intrinsic_matrix",
        "_extrinsic_matrix",
    )

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._bounds = Bounds(
            -1_000_000_000,
            -1_000_000_000,
            -1_000_000_000,
            1_000_000_000,
            1_000_000_000,
            1_000_000_000,
        )
        self._location = Location(0.0, 0.0, 0.0)
        self._rotation = Rotation(0.0, 0.0)

        self._intrinsic_matrix = QMatrix4x4()
        self._extrinsic_matrix = None

    def _clamp_location(self, location: Location) -> Location:
        return Location(
            min(max(self._bounds.min_x, location.x), self._bounds.max_x),
            min(max(self._bounds.min_y, location.y), self._bounds.max_y),
            min(max(self._bounds.min_z, location.z), self._bounds.max_z),
        )

    @property
    def location(self) -> Location:
        """The location of the camera. (x, y, z)"""
        return self._location

    @location.setter
    def location(self, location: Location):
        """Set the location of the camera. (x, y, z)."""

        # Clamp location to the bounds.
        location = self._clamp_location(location)

        if location != self._location:
            self._location = location
            self._extrinsic_matrix = None
            self.location_changed.emit()
            self.extrinsics_changed.emit()
            self.transform_changed.emit()

    def _clamp_rotation(self, rotation: Rotation) -> Rotation:
        return Rotation(
            rotation.azimuth
            if -180 <= rotation.azimuth < 180
            else ((rotation.azimuth + 180) % 360) - 180,
            min(max(-90.0, rotation.elevation), 90.0),
        )

    @property
    def rotation(self) -> Rotation:
        """The rotation of the camera. (azimuth/yaw, elevation/pitch).
        This should behave the same as how Minecraft handles it.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: Rotation):
        """Set the rotation of the camera. (azimuth/yaw, elevation/pitch).
        azimuth (-180 to 180), elevation (-90 to 90)
        This should behave the same as how Minecraft handles it."""

        # Clamp rotation to the bounds
        rotation = self._clamp_rotation(rotation)

        if rotation != self._rotation:
            self._rotation = rotation
            self._extrinsic_matrix = None
            self.rotation_changed.emit()
            self.extrinsics_changed.emit()
            self.transform_changed.emit()

    def set_extrinsics(self, location: Location, rotation: Rotation):
        """Set the camera location and rotation in one property."""
        location = self._clamp_location(location)
        rotation = self._clamp_rotation(rotation)
        location_changed = location != self._location
        rotation_changed = rotation != self._rotation

        if location_changed:
            self._location = location
        if rotation_changed:
            self._rotation = rotation

        if location_changed or rotation_changed:
            self._extrinsic_matrix = None

            if location_changed:
                self.location_changed.emit()

            if rotation_changed:
                self.rotation_changed.emit()

            self.extrinsics_changed.emit()
            self.transform_changed.emit()

    def set_perspective_projection(
        self,
        vertical_fov: float,
        aspect_ratio: float,
        near_plane: float,
        far_plane: float,
    ):
        """Set the projection to perspective with the given settings."""
        self._intrinsic_matrix.setToIdentity()
        self._intrinsic_matrix.perspective(
            vertical_fov, aspect_ratio, near_plane, far_plane
        )
        self.intrinsics_changed.emit()
        self.transform_changed.emit()

    def set_ortho_projection(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        near_plane: float,
        far_plane: float,
    ):
        """Set the projection to orthographic with the given settings."""
        self._intrinsic_matrix.setToIdentity()
        self._intrinsic_matrix.ortho(left, right, bottom, top, near_plane, far_plane)
        self.intrinsics_changed.emit()
        self.transform_changed.emit()

    @property
    def intrinsic_matrix(self) -> QMatrix4x4:
        """The matrix storing all intrinsic parameters (FOV/aspect/projection/clipping)"""
        return self._intrinsic_matrix

    @property
    def extrinsic_matrix(self) -> QMatrix4x4:
        """The matrix storing all extrinsic parameters (location/rotation)"""
        if self._extrinsic_matrix is None:
            self._extrinsic_matrix = QMatrix4x4()
            location = self._location
            rotation = self._rotation
            self._extrinsic_matrix.rotate(rotation.elevation, 1, 0, 0)
            self._extrinsic_matrix.rotate(rotation.azimuth, 0, 1, 0)
            self._extrinsic_matrix.translate(-location.x, -location.y, -location.z)
        return self._extrinsic_matrix
