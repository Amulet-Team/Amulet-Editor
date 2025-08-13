#define QT_NO_SIGNALS_SLOTS_KEYWORDS

#include "chunk_geometry.hpp"

namespace Amulet {

ChunkGeometry::ChunkGeometry(
    std::shared_ptr<ChunkHandle> chunk_handle_,
    QMatrix4x4& transform)
    : chunk_handle(std::move(chunk_handle_))
    , model_transform(transform)
    , _changed_token(chunk_handle->changed.connect([this]() { _mark_changed(); }))
{
}

ChunkGeometry::~ChunkGeometry()
{
    chunk_handle->changed.disconnect(_changed_token);
}

bool ChunkGeometry::has_changed()
{
    std::lock_guard lock(_mutex);
    return _chunk_state != _geometry_state;
}

size_t ChunkGeometry::get_chunk_state()
{
    std::lock_guard lock(_mutex);
    return _chunk_state;
}

void ChunkGeometry::_mark_changed()
{
    {
        std::lock_guard lock(_mutex);
        _chunk_state++;
    }
}

std::unique_ptr<ChunkGLData> ChunkGeometry::set_geometry(
    size_t geometry_state,
    std::unique_ptr<ChunkGLData> geometry_)
{
    std::lock_guard lock(_mutex);
    geometry.swap(geometry_);
    _geometry_state = geometry_state;
    return geometry_;
}

} // namespace Amulet
