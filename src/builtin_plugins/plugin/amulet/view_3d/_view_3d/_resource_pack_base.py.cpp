#include "_resource_pack_base.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

class PyAbstractOpenGLResourcePack : public Amulet::AbstractOpenGLResourcePack {
    using Amulet::AbstractOpenGLResourcePack::AbstractOpenGLResourcePack;

    const Amulet::BlockMesh _get_block_model(const Amulet::BlockStack& block_stack) override
    {
        PYBIND11_OVERRIDE_PURE(
            const Amulet::BlockMesh, /* Return type */
            Amulet::AbstractOpenGLResourcePack, /* Parent class */
            _get_block_model, /* Name of function in C++ (must match Python name) */
            block_stack /* Argument(s) */
        );
    }
};

void init_resource_pack_base(py::module m_parent)
{
    auto m = m_parent.def_submodule("_resource_pack_base");
    py::module::import("amulet.resource_pack");
    
    py::class_<Amulet::AbstractOpenGLResourcePack, PyAbstractOpenGLResourcePack>
        AbstractOpenGLResourcePack(m, "AbstractOpenGLResourcePack");

    AbstractOpenGLResourcePack.def(py::init<>());
    AbstractOpenGLResourcePack.def_readwrite(
        "_default_texture_bounds",
        &Amulet::AbstractOpenGLResourcePack::_default_texture_bounds);
    AbstractOpenGLResourcePack.def_readwrite(
        "_texture_bounds",
        &Amulet::AbstractOpenGLResourcePack::_texture_bounds);
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
}
