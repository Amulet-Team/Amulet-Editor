from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QMatrix4x4

from plugin.amulet.camera import CameraExtrinsics, Location, Rotation


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

    _extrinsics: CameraExtrinsics
    _intrinsic_matrix: QMatrix4x4

    __slots__ = (
        "_intrinsic_matrix",
        "_extrinsics",
    )

    def __init__(self, camera_extrinsics: CameraExtrinsics) -> None:
        super().__init__()
        self._extrinsics = camera_extrinsics
        self._intrinsic_matrix = QMatrix4x4()

        self._extrinsics.location_changed.connect(self.location_changed)
        self._extrinsics.rotation_changed.connect(self.rotation_changed)
        self._extrinsics.transform_changed.connect(self.extrinsics_changed)
        self._extrinsics.transform_changed.connect(self.transform_changed)

    @property
    def speed(self) -> float:
        """The speed of the camera in blocks per second."""
        return self._extrinsics.speed

    @speed.setter
    def speed(self, speed: float) -> None:
        self._extrinsics.speed = speed

    @property
    def location(self) -> Location:
        """The location of the camera. (x, y, z)"""
        return self._extrinsics.location

    @location.setter
    def location(self, location: Location) -> None:
        """Set the location of the camera. (x, y, z)."""
        self._extrinsics.location = location

    @property
    def rotation(self) -> Rotation:
        """The rotation of the camera. (azimuth/yaw, elevation/pitch).
        This should behave the same as how Minecraft handles it.
        """
        return self._extrinsics.rotation

    @rotation.setter
    def rotation(self, rotation: Rotation) -> None:
        """Set the rotation of the camera. (azimuth/yaw, elevation/pitch).
        azimuth (-180 to 180), elevation (-90 to 90)
        This should behave the same as how Minecraft handles it."""
        self._extrinsics.rotation = rotation

    def set_extrinsics(self, location: Location, rotation: Rotation) -> None:
        """Set the camera location and rotation in one property."""
        self._extrinsics.set_extrinsics(location, rotation)

    def set_perspective_projection(
        self,
        vertical_fov: float,
        aspect_ratio: float,
        near_plane: float,
        far_plane: float,
    ) -> None:
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
    ) -> None:
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
        return self._extrinsics.matrix
