#define QT_NO_SIGNALS_SLOTS_KEYWORDS

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/typing.h>

#include <amulet/pybind11_extensions/builtins.hpp>

#include <amulet/utils/event.py.hpp>

#include "level_geometry.hpp"

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

void init_level_geometry(py::module m_parent)
{
    auto m = m_parent.def_submodule("level_geometry");

    auto getCppPointer = py::module::import("shiboken6").attr("getCppPointer");

    py::classh<Amulet::LevelGeometry> LevelGeometry(m, "LevelGeometry");
    LevelGeometry.def(
        py::init<std::shared_ptr<Amulet::Level>>());
    LevelGeometry.def(
        "wake",
        &Amulet::LevelGeometry::wake,
        py::call_guard<py::gil_scoped_release>());
    LevelGeometry.def(
        "sleep",
        &Amulet::LevelGeometry::sleep,
        py::call_guard<py::gil_scoped_release>());
    LevelGeometry.def(
        "destroy_gl",
        &Amulet::LevelGeometry::destroy_gl,
        py::call_guard<py::gil_scoped_release>());
    LevelGeometry.def(
        "init_gl",
        &Amulet::LevelGeometry::init_gl,
        py::call_guard<py::gil_scoped_release>());
    LevelGeometry.def(
        "paint_gl",
        [getCppPointer](
            Amulet::LevelGeometry& self,
            pyext::PyObjectStr<"PySide6.QtGui.QMatrix4x4"> py_projection_matrix,
            pyext::PyObjectStr<"PySide6.QtGui.QMatrix4x4"> py_view_matrix) {
            py::tuple projection_matrix_ptrs = getCppPointer(py_projection_matrix);
            QMatrix4x4* projection_matrix = (QMatrix4x4*)projection_matrix_ptrs[0].cast<size_t>();
            py::tuple view_matrix_ptrs = getCppPointer(py_view_matrix);
            QMatrix4x4* view_matrix = (QMatrix4x4*)view_matrix_ptrs[0].cast<size_t>();
            {
                py::gil_scoped_release nogil;
                self.paint_gl(*projection_matrix, *view_matrix);
            }
        });
    LevelGeometry.def(
        "set_resource_pack",
        &Amulet::LevelGeometry::set_resource_pack,
        py::call_guard<py::gil_scoped_release>(),
        py::arg("resource_pack"));
    LevelGeometry.def(
        "set_dimension",
        &Amulet::LevelGeometry::set_dimension,
        py::call_guard<py::gil_scoped_release>(),
        py::arg("dimension"));
    LevelGeometry.def(
        "set_location",
        &Amulet::LevelGeometry::set_location,
        py::call_guard<py::gil_scoped_release>(),
        py::arg("cx"),
        py::arg("cz"));
    LevelGeometry.def(
        "set_render_distance",
        &Amulet::LevelGeometry::set_render_distance,
        py::call_guard<py::gil_scoped_release>(),
        py::arg("load_radius"),
        py::arg("unload_radius"));
    LevelGeometry.def_property_readonly(
        "geometry_changed",
        [](Amulet::LevelGeometry& self) -> Amulet::PyEvent<> {
            Amulet::create_event_binding<Amulet::Event<>>();
            return py::cast(self.get_geometry_changed(), py::return_value_policy::reference);
        },
        py::doc("Event emitted when the geometry changes."),
        py::keep_alive<0, 1>());
}
