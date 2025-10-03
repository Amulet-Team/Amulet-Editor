from __future__ import annotations

import time
from typing import Callable

from PySide6.QtCore import Qt, QEvent, QCoreApplication, QSize, QSignalBlocker, QTimer
from PySide6.QtGui import (
    QShowEvent,
    QHideEvent,
    QIcon,
    QGuiApplication,
    QPaintEvent,
    QPainter,
    QColor,
    QKeyEvent,
)
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
    QGridLayout,
    QDoubleSpinBox,
    QSizePolicy,
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

from plugin.amulet.selection import get_selection_manager


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
            width = max(
                0.0, min(1.0, (time.time() - self._start_time - 0.2) / self._dt)
            )
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
        self.update()


CuboidIcon = QIcon(tablericons.outline.cube)
EllipsoidIcon = QIcon(tablericons.outline.sphere)
UnknownIcon = QIcon(tablericons.outline.help_triangle)


class SelectionCoreWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._listening = False

        self._selection_manager = get_selection_manager()

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._selection_list = QListWidget()
        self._selection_list.currentRowChanged.connect(
            self._gui_selection_index_changed
        )
        self._layout.addWidget(self._selection_list)

        self._button_layout_1 = QHBoxLayout()
        self._layout.addLayout(self._button_layout_1)

        self._clone_button = QPushButton()
        self._clone_button.setIconSize(QSize(30, 30))
        self._clone_button.setIcon(QIcon(tablericons.outline.copy))
        self._clone_button.clicked.connect(self._clone_clicked)
        self._button_layout_1.addWidget(self._clone_button)

        self._delete_button = HeldPushButton(1)
        self._delete_button.setIconSize(QSize(30, 30))
        self._delete_button.setIcon(QIcon(tablericons.outline.trash))
        self._delete_button.clicked.connect(self._delete_clicked)
        self._button_layout_1.addWidget(self._delete_button)

        self._clipboard_save = QPushButton()
        self._clipboard_save.setIconSize(QSize(30, 30))
        self._clipboard_save.setIcon(QIcon(tablericons.outline.download))
        self._clipboard_save.clicked.connect(self._save_clicked)
        self._button_layout_1.addWidget(self._clipboard_save)

        self._clipboard_load = QPushButton()
        self._clipboard_load.setIconSize(QSize(30, 30))
        self._clipboard_load.setIcon(QIcon(tablericons.outline.upload))
        self._clipboard_load.clicked.connect(self._load_clicked)
        self._button_layout_1.addWidget(self._clipboard_load)

        self._button_layout_2 = QHBoxLayout()
        self._layout.addLayout(self._button_layout_2)

        self._add_cuboid_button = QPushButton()
        self._add_cuboid_button.setIconSize(QSize(30, 30))
        self._add_cuboid_button.setIcon(QIcon(tablericons.outline.cube_plus))
        self._add_cuboid_button.clicked.connect(self._add_cuboid)
        self._button_layout_2.addWidget(self._add_cuboid_button)

        self._add_ellipsoid_button = QPushButton()
        self._add_ellipsoid_button.setIconSize(QSize(30, 30))
        self._add_ellipsoid_button.setIcon(QIcon(tablericons.outline.sphere_plus))
        self._add_ellipsoid_button.clicked.connect(self._add_ellipsoid)
        self._button_layout_2.addWidget(self._add_ellipsoid_button)

        self._add_cylinder_button = QPushButton()
        self._add_cylinder_button.setIconSize(QSize(30, 30))
        self._add_cylinder_button.setIcon(QIcon(tablericons.outline.cylinder_plus))
        self._add_cylinder_button.setEnabled(False)
        # self._add_cylinder_button.clicked.connect(self._add_cylinder)
        self._button_layout_2.addWidget(self._add_cylinder_button)

        self._add_prism_button = QPushButton()
        self._add_prism_button.setIconSize(QSize(30, 30))
        self._add_prism_button.setIcon(QIcon(tablericons.outline.prism_plus))
        self._add_prism_button.setEnabled(False)
        # self._add_prism_button.clicked.connect(self._add_prism)
        self._button_layout_2.addWidget(self._add_prism_button)

        self._add_pyramid_button = QPushButton()
        self._add_pyramid_button.setIconSize(QSize(30, 30))
        self._add_pyramid_button.setIcon(QIcon(tablericons.outline.pyramid_plus))
        self._add_pyramid_button.setEnabled(False)
        # self._add_pyramid_button.clicked.connect(self._add_pyramid)
        self._button_layout_2.addWidget(self._add_pyramid_button)

        self._matrix_layout = QGridLayout()
        self._layout.addLayout(self._matrix_layout)
        self._matrix_entry: list[QDoubleSpinBox] = []

        def get_on_matrix_change(i_: int, j_: int) -> Callable[[float], None]:
            def on_matrix_change(value: float) -> None:
                with self._selection_manager.get_lock():
                    selection = self._selection_manager.get_selection()
                    index = self._selection_manager.get_selection_index()
                    if 0 <= index < len(selection):
                        selection[index].matrix.set_element(i_, j_, value)
                        self._selection_manager.set_selection(selection)

            return on_matrix_change

        for i in range(4):
            for j in range(4):
                spin = QDoubleSpinBox()
                spin.setDecimals(8)
                spin.setMinimum(-100_000_000)
                spin.setMaximum(100_000_000)
                spin.setSizePolicy(
                    QSizePolicy.Policy.Ignored, spin.sizePolicy().verticalPolicy()
                )
                spin.valueChanged.connect(get_on_matrix_change(i, j))
                self._matrix_layout.addWidget(spin, i, j)
                self._matrix_entry.append(spin)

        self._localise()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selection()

    def _add_shape(self, shape: SelectionShape) -> None:
        item = QListWidgetItem()
        if isinstance(shape, SelectionCuboid):
            item.setIcon(CuboidIcon)
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
            item.setIcon(EllipsoidIcon)
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
            item.setIcon(UnknownIcon)
            text = repr(shape)
        item.setText(text)
        self._selection_list.addItem(item)

    def _populate_gui(self) -> None:
        with QSignalBlocker(self._selection_list):
            selection = self._selection_manager.get_selection()
            self._selection_list.clear()
            for shape in selection:
                self._add_shape(shape)
            index = self._selection_manager.get_selection_index()
            if 0 <= index:
                self._selection_list.setCurrentRow(index)

        has_selection = bool(selection)
        self._clone_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        if 0 <= index:
            self._update_item(selection[index])
        else:
            self._update_item(None)

    def _update_item(self, shape: SelectionShape | None) -> None:
        if shape is None:
            for spin in self._matrix_entry:
                spin.setEnabled(False)
        else:
            for i in range(4):
                for j in range(4):
                    spin = self._matrix_entry[i * 4 + j]
                    spin.setEnabled(True)
                    spin.setValue(shape.matrix.get_element(i, j))

    def _clone_clicked(self) -> None:
        current_row = self._selection_list.currentRow()
        with self._selection_manager.get_lock():
            shapes = []
            for i, item in enumerate(self._selection_manager.get_selection()):
                shapes.append(item)
                if i == current_row:
                    shapes.append(item)
            selection = SelectionShapeGroup(shapes)
            self._selection_manager.set_selection(selection)

    def _delete_selection(self) -> None:
        current_row = self._selection_list.currentRow()
        with self._selection_manager.get_lock():
            selection = SelectionShapeGroup(
                [
                    item
                    for i, item in enumerate(self._selection_manager.get_selection())
                    if i != current_row
                ]
            )
            self._selection_manager.set_selection(selection)

    def _delete_clicked(self) -> None:
        current_row = self._selection_list.currentRow()
        with self._selection_manager.get_lock():
            if self._delete_button.was_held:
                selection = SelectionShapeGroup()
            else:
                selection = SelectionShapeGroup(
                    [
                        item
                        for i, item in enumerate(
                            self._selection_manager.get_selection()
                        )
                        if i != current_row
                    ]
                )
            self._selection_manager.set_selection(selection)

    def _add_cuboid(self) -> None:
        with self._selection_manager.get_lock():
            selection = SelectionShapeGroup(
                list(self._selection_manager.get_selection())
                + [SelectionCuboid(0, 0, 0, 1, 1, 1)]
            )
            self._selection_manager.set_selection(selection)
            self._selection_manager.set_selection_index(len(selection) - 1)

    def _add_ellipsoid(self) -> None:
        with self._selection_manager.get_lock():
            selection = SelectionShapeGroup(
                list(self._selection_manager.get_selection())
                + [SelectionEllipsoid(0, 0, 0, 0.5)]
            )
            self._selection_manager.set_selection(selection)
            self._selection_manager.set_selection_index(len(selection) - 1)

    def _save_clicked(self) -> None:
        text = self._selection_manager.get_selection().serialise()
        QGuiApplication.clipboard().setText(text)

    def _load_clicked(self) -> None:
        with CatchExceptionDialog("Failed parsing selection from clipboard."):
            selection = SelectionShapeGroup.deserialise(
                QGuiApplication.clipboard().text()
            )
            self._selection_manager.set_selection(selection)

    def _data_selection_index_changed(self, index: int) -> None:
        if index != self._selection_list.currentRow():
            self._selection_list.setCurrentRow(index)
        if 0 <= index:
            self._update_item(self._selection_manager.get_selection()[index])
        else:
            self._update_item(None)

    def _gui_selection_index_changed(self, index: int) -> None:
        self._selection_manager.set_selection_index(index)

    def showEvent(self, event: QShowEvent, /) -> None:
        if not self._listening:
            self._selection_manager.selection_changed.connect(
                self._populate_gui, Qt.ConnectionType.QueuedConnection
            )
            self._selection_manager.selection_index_changed.connect(
                self._data_selection_index_changed, Qt.ConnectionType.QueuedConnection
            )
            self._listening = True
        with self._selection_manager.get_lock():
            self._populate_gui()
            self._data_selection_index_changed(
                self._selection_manager.get_selection_index()
            )

    def hideEvent(self, event: QHideEvent, /) -> None:
        if self._listening:
            self._selection_manager.selection_changed.disconnect(self._populate_gui)
            self._selection_manager.selection_index_changed.disconnect(
                self._data_selection_index_changed
            )
            self._listening = False

    def _localise(self) -> None:
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
        self._clone_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "clone_tip", None
            )
        )
        self._clipboard_save.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "clipboard_save_tip", None
            )
        )
        self._clipboard_load.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "clipboard_load_tip", None
            )
        )
        self._delete_button.setToolTip(
            QCoreApplication.translate(
                "plugin.amulet.editor.SelectionWidget", "delete_tip", None
            )
        )

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()


def _demo() -> None:
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

    selection_manager = get_selection_manager()

    def set_empty_shapes() -> None:
        selection_manager.set_selection(SelectionShapeGroup())

    def set_shapes() -> None:
        selection_manager.set_selection(
            SelectionShapeGroup(
                [SelectionCuboid(-1, -1, -1, 2, 2, 2), SelectionEllipsoid(10, 0, 0, 2)]
            )
        )

    def set_many_shapes() -> None:
        group = SelectionShapeGroup(
            [SelectionCuboid(-1, -1, -1, 2, 2, 2), SelectionEllipsoid(10, 0, 0, 2)]
            * 500
        )
        selection_manager.set_selection(group)

    def increment_index() -> None:
        size = len(selection_manager.get_selection())
        if size:
            selection_manager.set_selection_index(
                (selection_manager.get_selection_index() + 1) % size
            )
        else:
            selection_manager.set_selection_index(0)

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

    # selection_manager.selection_changed.connect(display_selection, Qt.ConnectionType.QueuedConnection)
    # selection_manager.selection_index_changed.connect(display_selection_index, Qt.ConnectionType.QueuedConnection)

    translator = Translator()
    translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(editor_plugin_path[0], "_resources", "lang"),
    )

    app = QApplication()
    QCoreApplication.installTranslator(translator)

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
