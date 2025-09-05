from __future__ import annotations

from threading import RLock
import time

from PySide6.QtCore import Qt, QEvent, QCoreApplication, QSize, QSignalBlocker, QTimer
from PySide6.QtGui import QShowEvent, QHideEvent, QIcon, QGuiApplication, QPaintEvent, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QGridLayout,
    QLabel,
)

from plugin.tablericons import tablericons

from amulet.utils.cast import dynamic_cast
from amulet.utils.matrix import Matrix4x4
from amulet.core.selection import (
    SelectionShape,
    SelectionCuboid,
    SelectionEllipsoid,
    SelectionShapeGroup,
)

from amulet.app.exception import CatchExceptionDialog

import plugin.amulet.selection as selection_plugin


class HeldPushButton(QPushButton):
    def __init__(self, dt: float):
        super().__init__()
        self._dt = dt

        self._start_time = 0.0
        self._is_held = False
        self._held_completed = False

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self.update)

        self.pressed.connect(self._on_press)
        self.released.connect(self._on_release)

    @property
    def was_held(self) -> bool:
        """Was the button held for the required time."""
        return self._held_completed

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)

        if self._is_held:
            painter = QPainter(self)
            width = max(0.0, min(1.0, (time.time() - self._start_time - 0.2) / self._dt))
            painter.setBrush(QColor(100, 180, 255, 120))
            painter.setPen(Qt.PenStyle.NoPen)
            # TODO: rounded corners?
            painter.drawRect(0, 0, int(self.width() * width), self.height())

            if width == 1.0:
                self._timer.stop()

    def _on_press(self) -> None:
        self._start_time = time.time()
        self._is_held = True
        self._held_completed = False
        self._timer.start()

    def _on_release(self) -> None:
        self._is_held = False
        if self._start_time + self._dt + 0.2 <= time.time():
            self._held_completed = True
        self._timer.stop()


class SelectionCoreWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._lock = RLock()
        self._listening = False

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._selection_list = QListWidget()
        self._selection_list.currentRowChanged.connect(self._gui_selection_index_changed)
        self._layout.addWidget(self._selection_list)

        self._button_layout = QHBoxLayout()
        self._layout.addLayout(self._button_layout)

        self._add_cuboid_button = QPushButton()
        self._add_cuboid_button.setIconSize(QSize(30, 30))
        self._add_cuboid_button.setIcon(QIcon(tablericons.outline.cube_plus))
        self._add_cuboid_button.clicked.connect(self._add_cuboid)
        self._button_layout.addWidget(self._add_cuboid_button)

        self._add_ellipsoid_button = QPushButton()
        self._add_ellipsoid_button.setIconSize(QSize(30, 30))
        self._add_ellipsoid_button.setIcon(QIcon(tablericons.outline.sphere_plus))
        self._add_ellipsoid_button.clicked.connect(self._add_ellipsoid)
        self._button_layout.addWidget(self._add_ellipsoid_button)

        self._delete_button = HeldPushButton(1)
        self._delete_button.setIconSize(QSize(30, 30))
        self._delete_button.setIcon(QIcon(tablericons.outline.trash))
        self._delete_button.clicked.connect(self._delete_clicked)
        self._button_layout.addWidget(self._delete_button)

        self._copy_button = QPushButton()
        self._copy_button.setIconSize(QSize(30, 30))
        self._copy_button.setIcon(QIcon(tablericons.outline.copy))
        self._copy_button.clicked.connect(self._copy_clicked)
        self._button_layout.addWidget(self._copy_button)

        self._paste_button = QPushButton()
        self._paste_button.setIconSize(QSize(30, 30))
        self._paste_button.setIcon(QIcon(tablericons.outline.clipboard))
        self._paste_button.clicked.connect(self._paste_clicked)
        self._button_layout.addWidget(self._paste_button)

        self._localise()

    def _add_shape(self, shape: SelectionShape):
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, shape)
        if isinstance(shape, SelectionCuboid):
            item.setIcon(QIcon(tablericons.outline.cube))
            m = shape.matrix
            (sx, sy, sz), (rx, ry, rz), (dx, dy, dz) = m.decompose()
            m2 = Matrix4x4.transformation_matrix(sx, sy, sz, rx, ry, rz, dx, dy, dz)
            if m.almost_equal(m2):
                # can be decomposed to scale, rotation and displacement
                if rx == ry == rz == 0:
                    text = f"SelectionCuboid(min_x={dx}, min_y={dy}, min_z={dz}, size_x={sx}, size_y={sy}, size_z={sz})"
                else:
                    text = f"SelectionCuboid(transformation_matrix(sx={sx}, sy={sy}, sz={sz}, rx={rx}, ry={ry}, rz={rz}, dx={dx}, dy={dy}, dz={dz}))"
            else:
                text = (
                    f"SelectionCuboid(Matrix4x4(("
                    f"({m.get_element(0, 0)}, {m.get_element(0, 1)}, {m.get_element(0, 2)}, {m.get_element(0, 3)}), "
                    f"({m.get_element(1, 0)}, {m.get_element(1, 1)}, {m.get_element(1, 2)}, {m.get_element(1, 3)}), "
                    f"({m.get_element(2, 0)}, {m.get_element(2, 1)}, {m.get_element(2, 2)}, {m.get_element(2, 3)}), "
                    f"({m.get_element(3, 0)}, {m.get_element(3, 1)}, {m.get_element(3, 2)}, {m.get_element(3, 3)})"
                    f")))"
                )
        elif isinstance(shape, SelectionEllipsoid):
            item.setIcon(QIcon(tablericons.outline.sphere))
            m = shape.matrix
            (sx, sy, sz), (rx, ry, rz), (dx, dy, dz) = m.decompose()
            m2 = Matrix4x4.transformation_matrix(sx, sy, sz, rx, ry, rz, dx, dy, dz)
            if sx == sy == sz and m.almost_equal(m2):
                text = f"SelectionEllipsoid(x={dx}, y={dy}, z={dz}, radius={sx / 2.0})"
            else:
                text = (
                    f"SelectionEllipsoid(Matrix4x4(("
                    f"({m.get_element(0, 0)}, {m.get_element(0, 1)}, {m.get_element(0, 2)}, {m.get_element(0, 3)}), "
                    f"({m.get_element(1, 0)}, {m.get_element(1, 1)}, {m.get_element(1, 2)}, {m.get_element(1, 3)}), "
                    f"({m.get_element(2, 0)}, {m.get_element(2, 1)}, {m.get_element(2, 2)}, {m.get_element(2, 3)}), "
                    f"({m.get_element(3, 0)}, {m.get_element(3, 1)}, {m.get_element(3, 2)}, {m.get_element(3, 3)})"
                    f")))"
                )
        else:
            item.setIcon(QIcon(tablericons.outline.help_triangle))
            text = repr(shape)
        item.setText(text)
        self._selection_list.addItem(item)

    def _data_selection_changed(self, selection: SelectionShapeGroup) -> None:
        with self._lock:
            with QSignalBlocker(self._selection_list):
                self._selection_list.clear()
                for shape in selection:
                    self._add_shape(shape)
                index = selection_plugin.get_selection_index()
                if 0 <= index:
                    self._selection_list.setCurrentRow(index)
            self._delete_button.setEnabled(bool(selection))

    def _set_selection(self) -> None:
        with self._lock:
            selection = SelectionShapeGroup(
                [
                    dynamic_cast(
                        self._selection_list.item(i).data(Qt.ItemDataRole.UserRole),
                        SelectionShape,
                    )
                    for i in range(self._selection_list.count())
                ]
            )
        selection_plugin.set_selection(selection)

    def _delete_clicked(self) -> None:
        with self._lock:
            if self._delete_button.was_held:
                selection = SelectionShapeGroup()
            else:
                selection = SelectionShapeGroup([
                    item for i, item in enumerate(selection_plugin.get_selection())
                    if i != self._selection_list.currentRow()
                ])
            selection_plugin.set_selection(selection)

    def _add_cuboid(self) -> None:
        with selection_plugin.get_lock():
            selection = SelectionShapeGroup(
                list(selection_plugin.get_selection()) + [SelectionCuboid(0, 0, 0, 1, 1, 1)]
            )
            selection_plugin.set_selection(selection)
            selection_plugin.set_selection_index(len(selection) - 1)

    def _add_ellipsoid(self) -> None:
        with selection_plugin.get_lock():
            selection = SelectionShapeGroup(
                list(selection_plugin.get_selection()) + [SelectionEllipsoid(0, 0, 0, 0.5)]
            )
            selection_plugin.set_selection(selection)
            selection_plugin.set_selection_index(len(selection) - 1)

    def _copy_clicked(self) -> None:
        text = selection_plugin.get_selection().serialise()
        QGuiApplication.clipboard().setText(text)

    def _paste_clicked(self) -> None:
        with CatchExceptionDialog("Failed parsing selection from clipboard."):
            selection = SelectionShapeGroup.deserialise(
                QGuiApplication.clipboard().text()
            )
            selection_plugin.set_selection(selection)

    def _data_selection_index_changed(self, index: int) -> None:
        if index != self._selection_list.currentRow():
            self._selection_list.setCurrentRow(index)

    def _gui_selection_index_changed(self, index: int) -> None:
        selection_plugin.set_selection_index(index)

    def showEvent(self, event: QShowEvent, /) -> None:
        if not self._listening:
            selection_plugin.selection_changed.connect(self._data_selection_changed, Qt.ConnectionType.QueuedConnection)
            selection_plugin.selection_index_changed.connect(self._data_selection_index_changed, Qt.ConnectionType.QueuedConnection)
            self._listening = True
        with selection_plugin.get_lock():
            self._data_selection_changed(selection_plugin.get_selection())
            self._data_selection_index_changed(selection_plugin.get_selection_index())

    def hideEvent(self, event: QHideEvent, /) -> None:
        if self._listening:
            selection_plugin.selection_changed.disconnect(self._data_selection_changed)
            selection_plugin.selection_index_changed.disconnect(self._data_selection_index_changed)
            self._listening = False

    def _localise(self) -> None:
        self._copy_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "copy_tip", None
            )
        )
        self._paste_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "paste_tip", None
            )
        )
        self._add_cuboid_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "add_cuboid_tip", None
            )
        )
        self._add_ellipsoid_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "add_ellipsoid_tip", None
            )
        )
        self._delete_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "delete_tip", None
            )
        )

    def changeEvent(self, event, /):
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()


def _demo():
    import os
    from PySide6.QtWidgets import QApplication, QPushButton
    from PySide6.QtCore import QLocale
    from amulet.core.selection import (
        SelectionCuboid,
        SelectionEllipsoid,
        SelectionShapeGroup,
    )
    from amulet.app.localisation import Translator
    from plugin.amulet.editor import __path__ as editor_plugin_path

    def set_empty_shapes():
        selection_plugin.set_selection(SelectionShapeGroup())

    def set_shapes():
        selection_plugin.set_selection(
            SelectionShapeGroup(
                [SelectionCuboid(-1, -1, -1, 2, 2, 2), SelectionEllipsoid(10, 0, 0, 2)]
            )
        )

    def set_many_shapes():
        group = SelectionShapeGroup(
            [SelectionCuboid(-1, -1, -1, 2, 2, 2), SelectionEllipsoid(10, 0, 0, 2)] * 1000
        )
        selection_plugin.set_selection(group)

    def increment_index():
        size = len(selection_plugin.get_selection())
        if size:
            selection_plugin.set_selection_index((selection_plugin.get_selection_index() + 1) % size)
        else:
            selection_plugin.set_selection_index(0)

    class SelectionSetter(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout()
            self.setLayout(self._layout)

            self._set_empty_shapes = QPushButton("Set Empty Shapes")
            self._set_empty_shapes.clicked.connect(set_empty_shapes)
            self._layout.addWidget(self._set_empty_shapes)

            self._set_shapes = QPushButton("Set Shapes")
            self._set_shapes.clicked.connect(set_shapes)
            self._layout.addWidget(self._set_shapes)

            self._set_many_shapes = QPushButton("Set Many Shapes")
            self._set_many_shapes.clicked.connect(set_many_shapes)
            self._layout.addWidget(self._set_many_shapes)

            self._increment_index = QPushButton("Increment Index")
            self._increment_index.clicked.connect(increment_index)
            self._layout.addWidget(self._increment_index)

    set_shapes()

    # def display_selection(selection: SelectionShapeGroup) -> None:
    #     print(selection)
    #
    # def display_selection_index(index: int) -> None:
    #     print(f"selection_index={index}")

    # selection_plugin.selection_changed.connect(display_selection, Qt.ConnectionType.QueuedConnection)
    # selection_plugin.selection_index_changed.connect(display_selection_index, Qt.ConnectionType.QueuedConnection)

    translator = Translator()
    translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(editor_plugin_path[0], "_resources", "lang"),
    )

    app = QApplication()
    QCoreApplication.installTranslator(translator)
    app.setStyle("fusion")

    widget1 = SelectionCoreWidget()
    widget1.show()

    widget2 = SelectionCoreWidget()
    widget2.show()
    widget2.move(widget1.geometry().topRight())

    manager = SelectionSetter()
    manager.show()
    manager.move(widget2.geometry().topRight())

    app.exec()


if __name__ == "__main__":
    _demo()
