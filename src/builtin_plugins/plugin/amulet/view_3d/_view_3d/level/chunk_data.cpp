#include "chunk_data.hpp"

namespace Amulet {

ChunkData::ChunkData(
    std::shared_ptr<ChunkHandle> chunk_handle_,
    QMatrix4x4& transform)
    : chunk_handle(std::move(chunk_handle_))
    , model_transform(transform)
    , chunk_state(1)
    , geometry_state(0)
    , geometry(nullptr)
    , processing(false)
    , changed_token(chunk_handle->changed.connect([this]() { mark_changed(); }))
{
}

ChunkData::~ChunkData()
{
    chunk_handle->changed.disconnect(changed_token);
}

bool ChunkData::has_changed()
{
    std::lock_guard lock(_mutex);
    return chunk_state != geometry_state;
}

void ChunkData::mark_changed()
{
    {
        std::lock_guard lock(_mutex);
        chunk_state++;
    }
    changed.dispatch();
}

std::unique_ptr<ChunkGLData> ChunkData::set_geometry(
    size_t geometry_state_,
    std::unique_ptr<ChunkGLData> geometry_)
{
    std::lock_guard lock(_mutex);
    geometry.swap(geometry_);
    geometry_state = geometry_state_;
    return geometry_;
}

} // namespace Amulet
