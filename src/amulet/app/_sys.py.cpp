#include <pybind11/pybind11.h>

#include <stdexcept>

namespace py = pybind11;

/*
This code is rather janky.
CPython stores a reference to the modules mapping in sys.modules and in the C interpreter structure and uses both.
Python code is only able to overwrite the sys.modules attribute and not the C attribute.
The Python C API does not expose a way to set the C attribute.
This code steps through the interpreter state object until it finds an attribute equal to the sys.modules attribute and then overwrites it.
It also sets the sys.modules object.
I don't know how safe this is but it is the best solution I can find to actually swap out the sys.modules object.
*/

static PyObject** get_modules() {
    // Get the pointer to the sys.modules dictionary.
    PyObject* sys_modules = PyImport_GetModuleDict();
    if (sys_modules == nullptr) {
        // Make sure it has been initialised.
        throw std::runtime_error("sys.modules has not been initialised in the C API.");
    }

    // Get the interpreter state. It stores a pointer to the sys.modules object.
    PyInterpreterState* const interp = PyInterpreterState_Get();
    char* interp_char_ptr = reinterpret_cast<char*>(interp);
    char* interp_end = interp_char_ptr + 2000;

    // Iterate through the interpreter state memory until we find an attribute equal to sys_modules.
    for (; interp_char_ptr < interp_end; interp_char_ptr++) {
        PyObject** interp_obj_ptr = reinterpret_cast<PyObject**>(interp_char_ptr);
        if (*interp_obj_ptr == sys_modules) {
            // Return the pointer within the interpreters memory.
            return interp_obj_ptr;
        }
    }
    // If the sys.modules attribute was not found then the memory layout probably changed.
    throw std::runtime_error("Could not find sys.modules in the C API.");
}

static void set_sys_modules(py::object modules){
    PyObject** sys_modules = get_modules();
    PyObject* old_sys_modules = *sys_modules;
    py::module::import("sys").attr("modules") = modules;
    (*sys_modules) = modules.release().ptr();
    Py_XDECREF(old_sys_modules);
}

void init_sys(py::module m_parent) {
    auto m = m_parent.def_submodule("_sys");
    m.def("set_sys_modules", set_sys_modules);
}
