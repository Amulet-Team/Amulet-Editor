#pragma once

#include <memory>
#include <string>
#include <tuple>

#include <QOffscreenSurface>
#include <QOpenGLBuffer>
#include <QOpenGLContext>
#include <QOpenGLShaderProgram>
#include <QOpenGLVertexArrayObject>

#include <amulet/utils/event.hpp>
#include <amulet/utils/matrix.hpp>

#include <amulet/core/selection/shape_group.hpp>

namespace Amulet {

struct SelectionShapeGLData {
    size_t vertex_start;
    size_t vertex_count;
    Matrix4x4 matrix;
};

class SelectionGeometryGLData {
public:
    QOpenGLContext* context;
    QOffscreenSurface surface;
    QOpenGLShaderProgram program;
    int transformation_matrix_location;
    int model_matrix_location;

    QOpenGLVertexArrayObject vao;
    QOpenGLBuffer vbo;

    std::vector<SelectionShapeGLData> model_data;

    SelectionGeometryGLData(QOpenGLContext*);
};

class SelectionGeometryImp {
private:
    std::unique_ptr<SelectionGeometryGLData> _gl_data;
    Event<> geometry_changed;

    void init_geometry(const std::string&, std::vector<SelectionShapeGLData>);

public:
    SelectionGeometryImp();
    ~SelectionGeometryImp();

    SelectionGeometryImp(const SelectionGeometryImp&) = delete;
    SelectionGeometryImp(SelectionGeometryImp&&) = delete;
    SelectionGeometryImp& operator=(const SelectionGeometryImp&) = delete;
    SelectionGeometryImp& operator=(SelectionGeometryImp&&) = delete;

    void init_gl();
    void destroy_gl();
    void paint_gl(const Matrix4x4& projection_matrix, const Matrix4x4& view_matrix);

    Event<>& get_geometry_changed();

    void set_selection(const SelectionShapeGroup&);
};

} // namespace Amulet
