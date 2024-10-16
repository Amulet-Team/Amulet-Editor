#include <amulet/block.hpp>
#include <amulet/mesh/block/block_mesh.hpp>
#include <map>
#include <shared_mutex>
#include <string>
#include <tuple>
#include <unordered_map>

namespace Amulet {

class AbstractOpenGLResourcePack {
private:
    std::shared_mutex _mutex;

public:
    std::tuple<float, float, float, float> _default_texture_bounds;
    std::unordered_map<std::string, std::tuple<float, float, float, float>> _texture_bounds;
    std::map<Amulet::BlockStack, const Amulet::BlockMesh> _block_models;

    AbstractOpenGLResourcePack() { }

    const std::tuple<float, float, float, float>& texture_bounds(const std::string& texture_path)
    {
        const auto& it = _texture_bounds.find(texture_path);
        if (it == _texture_bounds.end()) {
            return _default_texture_bounds;
        } else {
            return it->second;
        }
    }

    virtual const Amulet::BlockMesh _get_block_model(const Amulet::BlockStack& block_stack) = 0;

    const Amulet::BlockMesh& get_block_model(const Amulet::BlockStack& block_stack)
    {
        std::shared_lock<std::shared_mutex> shared_lock(_mutex);
        const auto& it = _block_models.find(block_stack);
        if (it != _block_models.end()) {
            return it->second;
        }
        shared_lock.unlock();

        std::unique_lock<std::shared_mutex> unique_lock(_mutex);
        const auto& it2 = _block_models.find(block_stack);
        if (it2 != _block_models.end()) {
            return it2->second;
        }
        return _block_models.emplace(block_stack, _get_block_model(block_stack)).first->second;
    }
};

} // namespace Amulet
