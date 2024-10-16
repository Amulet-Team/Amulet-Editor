#include <pybind11/pybind11.h>
namespace py = pybind11;

void init_resource_pack_base(py::module);
void init_chunk_mesher(py::module);

static bool init_run = false;

void init_view_3d(py::module m)
{
    if (init_run) {
        return;
    }
    init_run = true;

    // This is normally added after initilsation but we need it to pass to subpackages.
    // This may cause issues with frozen installs.
    //m.attr("__path__") = py::module::import("importlib.util").attr("find_spec")("amulet_team_3d_viewer._view_3d").attr("submodule_search_locations");
    
    init_resource_pack_base(m);
    init_chunk_mesher(m);

    m.attr("View3D") = py::module::import("amulet_team_3d_viewer._view_3d._widget").attr("View3D");
}

PYBIND11_MODULE(__init__, m) { init_view_3d(m); }
PYBIND11_MODULE(_view_3d, m) { init_view_3d(m); }
