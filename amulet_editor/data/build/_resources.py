import errno
import os

from amulet_editor.data import build, system


def find_resource(*rel_path: str):
    for resource_dir in resource_dirs:
        resource_path = os.path.join(resource_dir, *rel_path)
        if os.path.exists(resource_path):
            return os.path.realpath(resource_path)
    raise FileNotFoundError(
        errno.ENOENT, "Could not find resource", os.sep.join(rel_path)
    )


def get_resource_dirs() -> list[str]:
    resources = os.path.join(os.getcwd(), "src", "main", "resources")

    subdirs = ["base", "secret"]
    subdirs.append(system.get_system())
    if system.is_linux():
        if system.is_arch():
            subdirs.append("arch")
        elif system.is_fedora():
            subdirs.append("fedora")
        elif system.is_ubuntu():
            subdirs.append("ubuntu")

    result = [os.path.join(os.getcwd(), "src", "main", "icons")]
    result.extend(os.path.join(resources, subdir) for subdir in reversed(subdirs))
    return result


def get_resource(rel_path):
    if build.fbs_installed():
        from amulet_editor.application.context._amulet_context import AMULET_CONTEXT

        return AMULET_CONTEXT.get_resource(rel_path)
    else:
        return find_resource(rel_path)


resource_dirs = get_resource_dirs()
