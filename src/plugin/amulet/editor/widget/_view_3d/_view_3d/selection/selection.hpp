#pragma once

#include <amulet/utils/event.hpp>

namespace Amulet {

class Matrix4x4;
class SelectionShapeGroup;

class SelectionGeometryImp;

class SelectionGeometry {
private:
    SelectionGeometryImp* _impl;

public:
    SelectionGeometry();
    ~SelectionGeometry();

    SelectionGeometry(const SelectionGeometry&) = delete;
    SelectionGeometry(SelectionGeometry&&) = delete;
    SelectionGeometry& operator=(const SelectionGeometry&) = delete;
    SelectionGeometry& operator=(SelectionGeometry&&) = delete;

    void init_gl();
    void destroy_gl();
    void paint_gl(const Matrix4x4& projection_matrix, const Matrix4x4& view_matrix);

    Event<>& get_geometry_changed();

    void set_selection(const SelectionShapeGroup&);
};

} // namespace Amulet
