#define QT_NO_SIGNALS_SLOTS_KEYWORDS

#include <pybind11/pybind11.h>

#include <QtGlobal>

#include <amulet/pybind11_extensions/compatibility.hpp>
#include <amulet/pybind11_extensions/py_module.hpp>

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

void init_resource_pack_base(py::module);
void init_view_3d_level(py::module);
void init_view_3d_selection(py::module);

void init_module(py::module m)
{
    pyext::init_compiler_config(m);
    pyext::check_compatibility(py::module::import("amulet.level"), m);

    init_resource_pack_base(m);
    init_view_3d_level(m);
    init_view_3d_selection(m);

    m.def("_get_qt_version", []() { 
        return py::str(qVersion());
    });
}

PYBIND11_MODULE(_view_3d, m)
{
    m.def("init", &init_module);
}
