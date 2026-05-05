#include "selection.hpp"
#include "selection_p.hpp"

namespace Amulet {

SelectionGeometry::SelectionGeometry()
    : _impl(new SelectionGeometryImp())
{
}
SelectionGeometry::~SelectionGeometry()
{
    delete _impl;
}

void SelectionGeometry::init_gl()
{
    _impl->init_gl();
}

void SelectionGeometry::destroy_gl()
{
    _impl->destroy_gl();
}

void SelectionGeometry::paint_gl(const Matrix4x4& projection_matrix, const Matrix4x4& view_matrix)
{
    _impl->paint_gl(projection_matrix, view_matrix);
}

Event<>& SelectionGeometry::get_geometry_changed()
{
    return _impl->get_geometry_changed();
}

void SelectionGeometry::set_selection(const SelectionShapeGroup& selection)
{
    _impl->set_selection(selection);
}

} // namespace Amulet
