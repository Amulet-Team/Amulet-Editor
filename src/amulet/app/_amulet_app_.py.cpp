#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_sys(py::module);

void init_amulet_app(py::module m){
    py::module::import("amulet.app.app");
}
