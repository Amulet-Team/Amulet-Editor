import os
import importlib.util

from shared.generate_pybind_stubs import run

def get_module_path(name: str) -> str:
    spec = importlib.util.find_spec(name)
    assert spec is not None
    module_path = spec.origin
    assert module_path is not None
    return module_path

def get_package_dir(name: str) -> str:
    return os.path.dirname(get_module_path(name))

def main():
    path = get_package_dir("amulet_team_3d_viewer")
    src_path = os.path.dirname(path)
    run(src_path, "amulet_team_3d_viewer._view_3d")

if __name__ == '__main__':
    main()
