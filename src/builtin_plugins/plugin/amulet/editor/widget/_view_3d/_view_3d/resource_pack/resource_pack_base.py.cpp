#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "abc.hpp"

#include <amulet/pybind11_extensions/py_module.hpp>

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

class PyAbstractOpenGLResourcePack : public Amulet::AbstractOpenGLResourcePack, public py::trampoline_self_life_support {
    using Amulet::AbstractOpenGLResourcePack::AbstractOpenGLResourcePack;

    std::string get_texture_path(std::optional<std::string> namespace_, std::string relative_path) override
    {
        PYBIND11_OVERRIDE_PURE(
            std::string, /* Return type */
            Amulet::AbstractOpenGLResourcePack, /* Parent class */
            get_texture_path, /* Name of function in C++ (must match Python name) */
            namespace_, relative_path /* Argument(s) */
        );
    }

    const Amulet::BlockMesh _get_block_model(const Amulet::BlockStack& block_stack) override
    {
        PYBIND11_OVERRIDE_PURE(
            const Amulet::BlockMesh, /* Return type */
            Amulet::AbstractOpenGLResourcePack, /* Parent class */
            _get_block_model, /* Name of function in C++ (must match Python name) */
            block_stack /* Argument(s) */
        );
    }

    size_t _get_texture_ptr() override
    {
        PYBIND11_OVERRIDE_PURE(
            size_t, /* Return type */
            Amulet::AbstractOpenGLResourcePack, /* Parent class */
            _get_texture_ptr, /* Name of function in C++ (must match Python name) */
        );
    }
};

static void init_abc(py::module m_parent)
{
    auto m = m_parent.def_submodule("abc");

    py::module::import("amulet.resource_pack");

    py::classh<Amulet::AbstractOpenGLResourcePack, PyAbstractOpenGLResourcePack>
        AbstractOpenGLResourcePack(m, "AbstractOpenGLResourcePack");

    AbstractOpenGLResourcePack.def(py::init<>());
    AbstractOpenGLResourcePack.def_readwrite(
        "_default_texture_bounds",
        &Amulet::AbstractOpenGLResourcePack::_default_texture_bounds);
    AbstractOpenGLResourcePack.def_readwrite(
        "_texture_bounds",
        &Amulet::AbstractOpenGLResourcePack::_texture_bounds);
    AbstractOpenGLResourcePack.def(
        "get_texture_path",
        &Amulet::AbstractOpenGLResourcePack::get_texture_path,
        py::doc("Get the absolute path of the image from the relative components."));
    AbstractOpenGLResourcePack.def(
        "get_texture_bounds",
        &Amulet::AbstractOpenGLResourcePack::get_texture_bounds,
        py::doc("Get the bounding box of a given texture path."));
    AbstractOpenGLResourcePack.def(
        "_get_block_model",
        &Amulet::AbstractOpenGLResourcePack::_get_block_model,
        py::doc("abstractmethod to load the BlockMesh. Must be implemented by the subclass."));
    AbstractOpenGLResourcePack.def(
        "get_block_model",
        &Amulet::AbstractOpenGLResourcePack::get_block_model,
        py::doc(
            "Get the BlockMesh for the given BlockStack.\n"
            "The Block will be translated to the version format using the previously specified translator."));
    AbstractOpenGLResourcePack.def(
        "_get_texture_ptr",
        &Amulet::AbstractOpenGLResourcePack::_get_texture_ptr);
}

void init_resource_pack_base(py::module m_parent)
{
    auto m = pyext::def_subpackage(m_parent, "resource_pack");
    
    init_abc(m);

    auto m_wrapper = py::module_::import((m.attr("__name__").cast<std::string>() + ".resource_pack").c_str());
    m.attr("OpenGLResourcePack") = m_wrapper.attr("OpenGLResourcePack");
    m.attr("OpenGLResourcePackHandle") = m_wrapper.attr("OpenGLResourcePackHandle");
    m.attr("get_gl_resource_pack_container") = m_wrapper.attr("get_gl_resource_pack_container");
}
