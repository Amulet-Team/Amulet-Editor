#include <string_view>

#include <QCoreApplication>
#include <QMatrix4x4>
#include <QOpenGLContext>
#include <QOpenGLFunctions>
#include <QThread>
#include <QTimer>

#include <amulet/utils/logging.hpp>
#include <amulet/utils/matrix.hpp>
#include <amulet/utils/event.hpp>

#include <amulet/core/selection/box.hpp>
#include <amulet/core/selection/box_group.hpp>
#include <amulet/core/selection/cuboid.hpp>
#include <amulet/core/selection/ellipsoid.hpp>
#include <amulet/core/selection/shape_group.hpp>

#include "selection_p.hpp"

namespace Amulet {

SelectionGeometryGLData::SelectionGeometryGLData(QOpenGLContext* context)
    : context(context)
    , transformation_matrix_location(0)
    , model_matrix_location(0)
{
    surface.create();
}

SelectionGeometryImp::SelectionGeometryImp()
{
}
SelectionGeometryImp::~SelectionGeometryImp()
{
}

void SelectionGeometryImp::init_gl()
{
    debug("SelectionGeometry::init_gl()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("SelectionGeometry::init_gl must be called from main thread.");
    }

    auto* f = QOpenGLContext::currentContext()->functions();

    auto gl_data = std::make_unique<SelectionGeometryGLData>(QOpenGLContext::currentContext());

    // Initialise the shader
    auto& program = gl_data->program;
    program.addShaderFromSourceCode(
        QOpenGLShader::ShaderTypeBit::Vertex,
        R"(#version 150
        in vec3 position;

        uniform mat4 model_matrix;
        uniform mat4 transformation_matrix;

        out vec4 world_position;

        void main() {
            world_position = model_matrix * vec4(position, 1.0);
            gl_Position = transformation_matrix * vec4(position, 1.0);
        })");

    program.addShaderFromSourceCode(
        QOpenGLShader::ShaderTypeBit::Fragment,
        R"(#version 150

        in vec4 world_position;

        out vec4 out_colour;

        void main(){
            float x = floor(mod(world_position.x, 2.0));
            float y = floor(mod(world_position.y, 2.0));
            float z = floor(mod(world_position.z, 2.0));

            out_colour = vec4(0.5, 0.5, 0.5, 1.0);
            out_colour.rgb = out_colour.rgb * (1.0 - 0.03 * x) * (1.0 - 0.06 * y) * (1.0 - 0.04 * z);
        })");

    program.bindAttributeLocation("position", 0);
    program.link();
    program.bind();
    gl_data->transformation_matrix_location = program.uniformLocation("transformation_matrix");
    gl_data->model_matrix_location = program.uniformLocation("model_matrix");
    program.release();

    auto& vao = gl_data->vao;
    auto& vbo = gl_data->vbo;

    // Create VAO
    vao.create();
    vao.bind();

    // Create VBO
    vbo.create();
    vbo.bind();
    vbo.allocate(0);

    // vertex coord
    f->glEnableVertexAttribArray(0);
    f->glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), 0);

    vbo.release();
    vao.release();

    _gl_data = std::move(gl_data);

    debug("SelectionGeometry::init_gl() end");
}

void SelectionGeometryImp::destroy_gl()
{
    debug("SelectionGeometry::destroy_gl()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("SelectionGeometry::destroy_gl must be called from main thread.");
    }

    // Destroy the OpenGL data.
    _gl_data = nullptr;

    debug("SelectionGeometry::destroy_gl() end");
}

void SelectionGeometryImp::paint_gl(const Matrix4x4& projection_matrix, const Matrix4x4& view_matrix)
{
    if (!_gl_data) {
        return;
    }

    if (QOpenGLContext::currentContext() != _gl_data->context) {
        throw std::runtime_error("Context is different.");
    }

    auto* f = QOpenGLContext::currentContext()->functions();

    // Set OpenGL attributes.
    f->glEnable(GL_DEPTH_TEST);
    f->glDepthFunc(GL_LEQUAL);
    f->glEnable(GL_BLEND);
    f->glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    f->glEnable(GL_CULL_FACE);
    f->glCullFace(GL_BACK);

    // Compute the transform
    Matrix4x4 transform = projection_matrix * view_matrix;

    // Bind the shader program
    auto& program = _gl_data->program;
    program.bind();
    auto& transformation_matrix_location = _gl_data->transformation_matrix_location;
    auto& model_matrix_location = _gl_data->model_matrix_location;

    _gl_data->vao.bind();

    auto camera_matrix = projection_matrix * view_matrix;

    for (const auto& shape_data : _gl_data->model_data) {
        // Set the real transformation matrix.
        auto model_matrix = shape_data.matrix;
        model_matrix.set_element(0, 3, model_matrix.get_element(0, 3) - 0.005);
        model_matrix.set_element(1, 3, model_matrix.get_element(1, 3) - 0.005);
        model_matrix.set_element(2, 3, model_matrix.get_element(2, 3) - 0.005);
        model_matrix.set_element(0, 0, model_matrix.get_element(0, 0) + 0.01);
        model_matrix.set_element(1, 1, model_matrix.get_element(1, 1) + 0.01);
        model_matrix.set_element(2, 2, model_matrix.get_element(2, 2) + 0.01);
        auto q_matrix = (camera_matrix * model_matrix).get_qt_matrix();
        program.setUniformValue(transformation_matrix_location, q_matrix);

        // Set the model matrix with transform wrapped to the range 0-2
        // This is used to find the colour
        auto checker_model_matrix = shape_data.matrix.get_qt_matrix();
        checker_model_matrix(0, 3) = std::fmod(checker_model_matrix(0, 3), 2.0f) + 0.001;
        checker_model_matrix(1, 3) = std::fmod(checker_model_matrix(1, 3), 2.0f) + 0.001;
        checker_model_matrix(2, 3) = std::fmod(checker_model_matrix(2, 3), 2.0f) + 0.001;
        checker_model_matrix(0, 0) = checker_model_matrix(0, 0) - 0.002;
        checker_model_matrix(1, 1) = checker_model_matrix(1, 1) - 0.002;
        checker_model_matrix(2, 2) = checker_model_matrix(2, 2) - 0.002;
        program.setUniformValue(model_matrix_location, checker_model_matrix);

        // Draw the shape
        f->glDrawArrays(GL_TRIANGLES, shape_data.vertex_start, shape_data.vertex_count);
    }

    _gl_data->vao.release();

    program.release();
}

Event<>& SelectionGeometryImp::get_geometry_changed() {
    return geometry_changed;
}

void SelectionGeometryImp::init_geometry(const std::string& buffer, std::vector<SelectionShapeGLData> model_data)
{
    debug("SelectionGeometry::init_geometry()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("SelectionGeometry::init_geometry must be called from main thread.");
    }

    if (!_gl_data) {
        // _gl_data has not been initialised or has been destroyed.
        return;
    }

    // TODO: There is a race condition here
    // If set_selection is called twice in parallel and
    // the second finishes meshing first, the first will win.
    // We want the later call to win.

    if (!_gl_data->context->makeCurrent(&_gl_data->surface)) {
        throw std::runtime_error("Could not make context current.");
    }

    _gl_data->vbo.bind();
    _gl_data->vbo.allocate(buffer.data(), buffer.size());
    _gl_data->vbo.release();

    _gl_data->model_data = std::move(model_data);

    _gl_data->context->doneCurrent();

    // Notify listeners that the geometry changed
    geometry_changed.dispatch();
}

static const float cube_vertices[] = { 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f };

void SelectionGeometryImp::set_selection(const SelectionShapeGroup& shapes)
{
    // compute mesh
    std::string buffer;
    std::vector<SelectionShapeGLData> model_data;

    // Native shape
    // for (const auto& shape : shapes) {
    //     // TODO: This should be a virtual function on the shape
    //     if (auto* cuboid = dynamic_cast<SelectionCuboid*>(shape.get())) {
    //         std::string_view shape_buffer(reinterpret_cast<const char*>(cube_vertices), sizeof(cube_vertices));
    //         size_t start = buffer.size() / (3 * sizeof(float));
    //         size_t count = shape_buffer.size() / (3 * sizeof(float));
    //         buffer += shape_buffer;
    //         model_data.emplace_back(start, count, cuboid->get_matrix());
    //     } else if (auto* cuboid = dynamic_cast<SelectionCuboid*>(shape.get())) {
    //     }
    // }

    // Voxelised shape
    for (const auto& shape : shapes) {
        auto boxes = shape->voxelise();
        for (const auto& box : boxes) {
            std::string_view shape_buffer(reinterpret_cast<const char*>(cube_vertices), sizeof(cube_vertices));
            size_t start = buffer.size() / (3 * sizeof(float));
            size_t count = shape_buffer.size() / (3 * sizeof(float));
            buffer += shape_buffer;
            auto matrix = Matrix4x4::translation_matrix(box.min_x(), box.min_y(), box.min_z()) * Matrix4x4::scale_matrix(box.size_x(), box.size_y(), box.size_z());
            model_data.emplace_back(start, count, matrix);
        }
    }

    info(std::to_string(model_data.size()));

    // Call
    QTimer* timer = new QTimer();
    timer->moveToThread(QCoreApplication::instance()->thread());
    timer->setSingleShot(true);
    QObject::connect(timer, &QTimer::timeout, [this, timer, buffer = std::move(buffer), model_data = std::move(model_data)]() {
        // main thread
        init_geometry(buffer, std::move(model_data));
        timer->deleteLater();
    });
    QMetaObject::invokeMethod(timer, "start", Qt::QueuedConnection, Q_ARG(int, 0));
}

} // namespace Amulet
