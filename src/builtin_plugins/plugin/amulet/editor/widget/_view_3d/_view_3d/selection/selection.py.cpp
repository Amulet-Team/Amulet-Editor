#include <pybind11/pybind11.h>

#include <amulet/pybind11_extensions/py_module.hpp>

#include <amulet/utils/event.py.hpp>
#include <amulet/utils/matrix.hpp>

#include <amulet/core/selection/shape_group.hpp>

#include "selection.hpp"

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

void init_view_3d_selection(py::module m_parent)
{
    auto m = pyext::def_subpackage(m_parent, "selection");

    py::classh<Amulet::SelectionGeometry> SelectionGeometry(m, "SelectionGeometry",
        "A class to maintain the OpenGL state of a selection.");

    SelectionGeometry.def(py::init());

    SelectionGeometry.def(
        "init_gl",
        &Amulet::SelectionGeometry::init_gl,
        py::doc("Initialise the OpenGL state.\nThis must be called with an active OpenGL context."));

    SelectionGeometry.def(
        "destroy_gl",
        &Amulet::SelectionGeometry::destroy_gl,
        py::doc("Destroy the OpenGL state.\nThis must be called with the same active OpenGL context used when init_gl was called."));

    SelectionGeometry.def(
        "paint_gl",
        &Amulet::SelectionGeometry::paint_gl,
        py::doc("Paint the selection.\nThis must be called with the same active OpenGL context used when init_gl was called."),
        py::arg("projection_matrix"),
        py::arg("view_matrix"));

    Amulet::def_event(
        SelectionGeometry,
        "geometry_changed",
        &Amulet::SelectionGeometry::get_geometry_changed
        );

    SelectionGeometry.def(
        "set_selection",
        &Amulet::SelectionGeometry::set_selection,
        py::doc("Set the new selection shape group.\nThis is thread safe."),
        py::arg("selection_group"));
}
