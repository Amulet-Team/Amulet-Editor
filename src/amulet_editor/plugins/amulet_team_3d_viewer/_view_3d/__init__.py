from typing import Optional
import random

from PySide6.QtCore import Signal, Property, Qt
from PySide6.QtGui import QMatrix4x4, QQuaternion, QVector3D
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DInput import Qt3DInput, QIntList
from PySide6.Qt3DRender import Qt3DRender
from PySide6.Qt3DLogic import Qt3DLogic

from amulet_team_main_window.application.windows.main_window import View
from ._3d_widget import Qt3DWidget


class AbstractCameraController(Qt3DCore.QEntity):
    def __init__(self, parent):
        super().__init__(parent)

        self._frame_action = Qt3DLogic.QFrameAction()
        self._frame_action.triggered.connect(self.move_camera)
        self.addComponent(self._frame_action)

    def move_camera(self, dt: float):
        raise NotImplementedError


class CameraController(AbstractCameraController):
    def __init__(self, parent):
        super().__init__(parent)

        self._camera: Optional[Qt3DRender.QCamera] = None
        self._linear_speed = 1.0
        self._look_speed = 1.0

        self._keyboard = Qt3DInput.QKeyboardDevice()
        self._mouse = Qt3DInput.QMouseDevice()
        self._logical_device = Qt3DInput.QLogicalDevice()

        self._left_input = Qt3DInput.QButtonAxisInput()
        self._left_input.setScale(-1.0)
        self._left_input.setSourceDevice(self._keyboard)

        self._right_input = Qt3DInput.QButtonAxisInput()
        self._right_input.setScale(1.0)
        self._right_input.setSourceDevice(self._keyboard)

        self._horizontal_axis = Qt3DInput.QAxis()
        self._horizontal_axis.addInput(self._left_input)
        self._horizontal_axis.addInput(self._right_input)
        self._logical_device.addAxis(self._horizontal_axis)

        self._forwards_input = Qt3DInput.QButtonAxisInput()
        self._forwards_input.setScale(1.0)
        self._forwards_input.setSourceDevice(self._keyboard)

        self._backwards_input = Qt3DInput.QButtonAxisInput()
        self._backwards_input.setScale(-1.0)
        self._backwards_input.setSourceDevice(self._keyboard)

        self._planar_axis = Qt3DInput.QAxis()
        self._logical_device.addAxis(self._planar_axis)
        self._planar_axis.addInput(self._forwards_input)
        self._planar_axis.addInput(self._backwards_input)

        self._up_input = Qt3DInput.QButtonAxisInput()
        self._up_input.setScale(1.0)
        self._up_input.setSourceDevice(self._keyboard)

        self._down_input = Qt3DInput.QButtonAxisInput()
        self._down_input.setScale(-1.0)
        self._down_input.setSourceDevice(self._keyboard)
        self._vertical_axis = Qt3DInput.QAxis()
        self._vertical_axis.addInput(self._down_input)
        self._vertical_axis.addInput(self._up_input)
        self._logical_device.addAxis(self._vertical_axis)

        self._look_x_input = Qt3DInput.QAnalogAxisInput()
        self._look_x_input.setAxis(0)  # Qt3DInput.QMouseDevice.Axis.X
        self._look_x_input.setSourceDevice(self._mouse)
        self._look_x_axis = Qt3DInput.QAxis()
        self._look_x_axis.addInput(self._look_x_input)
        self._logical_device.addAxis(self._look_x_axis)

        self._look_y_input = Qt3DInput.QAnalogAxisInput()
        self._look_y_input.setAxis(1)  # Qt3DInput.QMouseDevice.Axis.Y
        self._look_y_input.setSourceDevice(self._mouse)
        self._look_y_axis = Qt3DInput.QAxis()
        self._look_y_axis.addInput(self._look_y_input)
        self._logical_device.addAxis(self._look_y_axis)

        self._left_mouse_button_input = Qt3DInput.QActionInput()
        self._left_mouse_button_input.setButtons([1])  # Qt.MouseButton.LeftButton
        self._left_mouse_button_input.setSourceDevice(self._mouse)
        self._left_mouse_button_action = Qt3DInput.QAction()
        self._left_mouse_button_action.addInput(self._left_mouse_button_input)
        self._logical_device.addAction(self._left_mouse_button_action)

        self.enabledChanged.connect(self._logical_device.setEnabled)

        # Configure keys TODO: Find a way to configure this outside of code
        self._left_input.setButtons([Qt.Key.Key_J])
        self._right_input.setButtons([Qt.Key.Key_L])
        self._forwards_input.setButtons([Qt.Key.Key_I])
        self._backwards_input.setButtons([Qt.Key.Key_K])
        self._up_input.setButtons([Qt.Key.Key_Space])
        self._down_input.setButtons([Qt.Key.Key_Semicolon])

        self.addComponent(self._logical_device)

    def camera(self) -> Qt3DRender.QCamera:
        camera = self._camera
        if camera is None:
            raise RuntimeError("Camera has not been initialised")
        return camera

    def set_camera(self, camera: Qt3DRender.QCamera):
        if camera != self._camera:
            self._camera = camera
            self.camera_changed.emit()

    camera_changed = Signal()

    def linear_speed(self) -> float:
        return self._linear_speed

    def set_linear_speed(self, linear_speed: float):
        if self._linear_speed != linear_speed:
            self._linear_speed = linear_speed
            self.linear_speed_changed.emit()

    linear_speed_changed = Signal()

    def look_speed(self) -> float:
        return self._look_speed

    def set_look_speed(self, look_speed: float):
        if self._look_speed != look_speed:
            self._look_speed = look_speed
            self.look_speed_changed.emit()

    look_speed_changed = Signal()

    def move_camera(self, dt: float):
        camera = self.camera()
        camera.translate(
            QVector3D(
                self._horizontal_axis.value() * self.linear_speed(),
                self._vertical_axis.value() * self.linear_speed(),
                self._planar_axis.value() * self.linear_speed(),
            ) * dt
        )

        if self._left_mouse_button_action.isActive():
            look_speed = self.look_speed()
            up_vector = QVector3D(0.0, 1.0, 0.0)
            camera.pan(self._look_x_axis.value() * look_speed * dt, up_vector)
            camera.tilt(self._look_y_axis.value() * look_speed * dt)


class View3D(Qt3DWidget, View):
    def __init__(self):
        super().__init__()

        # Camera
        self.camera().lens().setPerspectiveProjection(45, 16 / 9, 0.1, 1000)
        self.camera().setPosition(QVector3D(0, 0, 40))
        self.camera().setViewCenter(QVector3D(0, 0, 0))

        # Root entity
        self.rootEntity = Qt3DCore.QEntity()

        # Material
        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self.rootEntity)

        # Torus
        self.torusEntity = Qt3DCore.QEntity(self.rootEntity)
        self.torusMesh = Qt3DExtras.QTorusMesh()
        self.torusMesh.setRadius(6)
        self.torusMesh.setMinorRadius(0.5)
        self.torusMesh.setRings(100)
        self.torusMesh.setSlices(20)

        self.torusTransform = Qt3DCore.QTransform()
        self.torusTransform.setScale3D(QVector3D(1.5, 1, 0.5))
        self.torusTransform.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), 45))

        self.torusEntity.addComponent(self.torusMesh)
        self.torusEntity.addComponent(self.torusTransform)
        self.torusEntity.addComponent(self.material)

        # Sphere
        self.sphereEntity = Qt3DCore.QEntity(self.rootEntity)
        self.sphereMesh = Qt3DExtras.QSphereMesh()
        self.sphereMesh.setRadius(3)

        self.sphereTransform = Qt3DCore.QTransform()

        self.sphereEntity.addComponent(self.sphereMesh)
        self.sphereEntity.addComponent(self.sphereTransform)
        self.sphereEntity.addComponent(self.material)

        self.spheres = []
        for _ in range(1000):
            sphere = Qt3DCore.QEntity(self.rootEntity)

            transform = Qt3DCore.QTransform()
            transform.setTranslation(
                QVector3D(
                    random.randrange(-5000, 5000) / 10,
                    random.randrange(-5000, 5000) / 10,
                    random.randrange(-5000, 5000) / 10,
                )
            )

            sphere.addComponent(self.sphereMesh)
            sphere.addComponent(transform)
            sphere.addComponent(self.material)

            self.spheres.append([
                sphere,
                transform
            ])

        # For camera controls
        self.camController = CameraController(self.rootEntity)
        self.camController.set_camera(self.camera())
        self.camController.set_linear_speed(50)
        self.camController.set_look_speed(180)

        self.setRootEntity(self.rootEntity)
