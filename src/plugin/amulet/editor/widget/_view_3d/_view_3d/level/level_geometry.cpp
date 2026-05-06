#define QT_NO_SIGNALS_SLOTS_KEYWORDS

#include <QCoreApplication>
#include <QTimer>

#include "level_geometry.hpp"
#include "level_geometry_p.hpp"

namespace Amulet {

LevelGeometry::LevelGeometry(std::shared_ptr<Level> level)
    : _impl(new LevelGeometryImp(std::move(level)))
{
}

LevelGeometry::~LevelGeometry()
{
    LevelGeometryImp* impl = _impl;

    // Delete later without inheriting QObject
    QTimer* timer = new QTimer();
    timer->moveToThread(QCoreApplication::instance()->thread());
    timer->setSingleShot(true);
    QObject::connect(timer, &QTimer::timeout, [impl, timer]() {
        try {
            // main thread
            delete impl;
            timer->deleteLater();
        } catch (const std::exception& e) {
            error(std::string("Error in ~LevelGeometry(): ") + e.what());
        } catch (...) {
            error("Error in ~LevelGeometry()");
        }
    });
    QMetaObject::invokeMethod(timer, "start", Qt::QueuedConnection, Q_ARG(int, 0));
}

void LevelGeometry::wake() { _impl->wake(); }

void LevelGeometry::sleep() { _impl->sleep(); }

void LevelGeometry::destroy_gl() { _impl->destroy_gl(); }

void LevelGeometry::init_gl() { _impl->init_gl(); }

void LevelGeometry::paint_gl(QMatrix4x4& projection_matrix, QMatrix4x4& view_matrix)
{
    _impl->paint_gl(projection_matrix, view_matrix);
}

void LevelGeometry::set_resource_pack(std::shared_ptr<AbstractOpenGLResourcePack> resource_pack)
{
    _impl->set_resource_pack(std::move(resource_pack));
}

void LevelGeometry::set_dimension(DimensionId dimension)
{
    _impl->set_dimension(dimension);
}
void LevelGeometry::set_location(std::int64_t cx, std::int64_t cz)
{
    _impl->set_location(cx, cz);
}
void LevelGeometry::set_render_distance(std::int64_t load_radius, std::int64_t unload_radius)
{
    _impl->set_render_distance(load_radius, unload_radius);
}

Event<>& LevelGeometry::get_geometry_changed()
{
    return _impl->geometry_changed;
}

} // namespace Amulet
