#include <pybind11/pybind11.h>

#include <amulet/pybind11_extensions/py_module.hpp>

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

void init_level_geometry(py::module);

void init_view_3d_level(py::module m_parent)
{
    auto m = pyext::def_subpackage(m_parent, "level");

    init_level_geometry(m);
}
