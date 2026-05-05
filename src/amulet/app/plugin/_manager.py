from __future__ import annotations

import inspect
from typing import Optional, Protocol
from types import FrameType, ModuleType
from threading import RLock
import os
import glob
import logging
from importlib.util import spec_from_file_location, module_from_spec
from importlib.metadata import version, packages_distributions
import sys
from collections.abc import Mapping, Sequence
import traceback
import builtins

from packaging.version import Version

from amulet.app.path._plugin import first_party_plugin_directory

from ._uid import LibraryUID
from ._state import PluginState
from ._container import PluginContainer
from ._requirement import Requirement
from amulet.app.exception import display_exception

log = logging.getLogger(__name__)
PythonVersion = Version(".".join(map(str, sys.version_info[:3])))

_packages_distributions: Optional[dict[str, list[str]]] = None


def _get_packages_distributions() -> dict[str, list[str]]:
    global _packages_distributions
    if _packages_distributions is None:
        _packages_distributions = dict(packages_distributions())
    return _packages_distributions


"""
Notes:
First party plugins are stored in plugin
Third party plugins are imported as a zip and extracted to a writable directory with a UUID as the name.
Custom code loads the plugin package into sys.modules under its package name.
TODO: look into generating stub files for the active plugins to help with development on the compiled version.
Plugins can import directly from other plugins to access static classes and functions 
"""


# A lock for the plugin data. Code must acquire this before touching the plugin data
_plugin_lock = RLock()

# The plugin data
_plugins: dict[LibraryUID, PluginContainer] = {}

# A map from the package identifier to the UID.
# Only plugins that are currently enabled will appear in this dictionary.
_enabled_plugins: dict[str, LibraryUID] = {}


_amulet_modules = {
    "amulet-io": ["amulet", "amulet.io"],
    "amulet-leveldb": ["amulet", "amulet.leveldb"],
    "amulet-utils": ["amulet", "amulet.utils"],
    "amulet-zlib": ["amulet", "amulet.zlib"],
    "amulet-nbt": ["amulet", "amulet.nbt"],
    "amulet-core": ["amulet", "amulet.core"],
    "amulet-game": ["amulet", "amulet.game"],
    "amulet-anvil": ["amulet", "amulet.anvil"],
    "amulet-level": ["amulet", "amulet.level"],
    "amulet-resource-pack": ["amulet", "amulet.resource_pack"],
    "amulet-editor": ["amulet", "amulet.app"],
}

_module_to_libraries: Optional[dict[str, set[str]]] = None


def _get_module_to_libraries() -> dict[str, set[str]]:
    global _module_to_libraries
    if _module_to_libraries is None:
        log.debug("Loading distribution information.")
        _module_to_libraries = {
            k: set(v) for k, v in _get_packages_distributions().items()
        }
        # if a module is installed in editable mode, the above won't work
        for dist_name, qualnames in _amulet_modules.items():
            for qualname in qualnames:
                _module_to_libraries.setdefault(qualname, set()).add(dist_name)
        log.debug(f"Finished loading distribution information.")
    return _module_to_libraries


def _module_qualname_to_libraries(qualname: str) -> set[str]:
    library_map = _get_module_to_libraries()
    qualname_split = qualname.split(".")
    libraries: set[str] = set()
    for i in range(1, len(qualname_split) + 1):
        new_libraries = library_map.get(".".join(qualname_split[:i]), set())
        if len(new_libraries) == 1:
            # module matches exactly one library. Return it.
            return {l.lower().replace("-", "_") for l in new_libraries}
        elif 1 < len(new_libraries):
            # module matches more than one library
            # try the nested module but fall back to this
            libraries = new_libraries
        else:
            # no matching modules. Use the previously saved value.
            break
    if libraries:
        return {l.lower().replace("-", "_") for l in libraries}
    raise RuntimeError(f"Could not find library for {qualname}")


PyModules = frozenset((*sys.builtin_module_names, *sys.stdlib_module_names))


def _validate_import(imported_name: str, frame: FrameType | None) -> None:
    # Plugins can only import libraries and plugins they have specified as a dependency.
    # Plugins can only be imported by other plugins.
    # We step back through the stack.
    # If we find a plugin that does not have the authority then we raise an error.
    # If we do not find a plugin in the stack we raise an error

    # Skip importlib frames
    while (
        frame is not None
        and frame.f_globals.get("__name__", "").split(".", 1)[0] == "importlib"
    ):
        frame = frame.f_back

    # Skip if the frame is None or the import was caused by this module.
    if frame is None or frame.f_globals.get("__name__") == __name__:
        return

    imported_name_split = imported_name.split(".", 3)
    if imported_name_split[0] in PyModules:
        # A built-in python module was imported.
        # Plugins don't need to specify native python libraries.
        return
    elif imported_name_split[0] == "plugin":
        # A plugin was imported.
        # The importer must be a plugin that specified it as a requirement.

        # Make sure a plugin was actually imported and not just the plugin namespace
        if len(imported_name_split) < 3:
            return

        # Get the imported plugin name.
        imported_plugin = f"{imported_name_split[1]}.{imported_name_split[2]}"

        # Get the plugin that imported it
        importer_name = frame.f_globals.get("__name__")
        if importer_name is None:
            raise RuntimeError(f"Could not find __name__ attribute for frame\n{frame}")
        importer_name_split = importer_name.split(".", 3)
        if importer_name_split[0] != "plugin" or len(importer_name_split) < 3:
            raise RuntimeError(
                f'Plugin module "{imported_name}" was imported by "{importer_name}". Plugins can only be imported by plugins.'
            )
        importer_plugin = f"{importer_name_split[1]}.{importer_name_split[2]}"

        # Plugins can import themselves
        if importer_plugin == imported_plugin:
            return

        # Validate that it has permission to import the plugin
        plugin_container = _plugins[_enabled_plugins[importer_plugin]]
        if any(
            dependency.identifier == imported_plugin
            for dependency in plugin_container.data.depends.plugin
        ):
            return

        # imported by a plugin that does not have the dependency listed
        raise RuntimeError(
            f"{importer_name} imported {imported_name} which it does not have authority for.\nYou must list a plugin dependency in your plugin's metadata to be able to import it."
        )

    else:
        # A third party library was imported
        # If it was imported by a plugin it must specify it as a requirement.

        # Get the module that imported it
        importer_name = frame.f_globals.get("__name__")
        if importer_name is None:
            raise RuntimeError(f"Could not find __name__ attribute for frame\n{frame}")
        importer_name_split = importer_name.split(".", 3)

        # Only plugins need to be validated.
        if importer_name_split[0] != "plugin" or len(importer_name_split) < 3:
            return

        # Find the importer plugin data.
        importer_plugin = f"{importer_name_split[1]}.{importer_name_split[2]}"
        plugin_container = _plugins[_enabled_plugins[importer_plugin]]

        # Find which package the import came from.
        package_names = _module_qualname_to_libraries(imported_name)

        # Validate that the plugin is allowed to import that package.
        if any(
            dependency.identifier in package_names
            for dependency in plugin_container.data.depends.library
        ):
            return

        raise RuntimeError(
            f"{importer_name} imported {imported_name} which it does not have authority for.\nYou must list a dependency in your plugin's metadata to be able to import it."
        )


class ImportProtocol(Protocol):
    def __call__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType: ...


def wrap_importer(imp: ImportProtocol) -> ImportProtocol:
    def wrap_importer_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_name = name
        elif 1 <= level:
            assert globals is not None
            module_src = globals["__name__"]
            assert isinstance(module_src, str)
            name_split = module_src.split(".")
            imported_name = f"{'.'.join(name_split[:len(name_split)-level+1])}.{name}"
        else:
            raise ValueError("level must be 0 or larger")
        frame = inspect.currentframe()
        if frame is not None:
            _validate_import(imported_name, frame.f_back)
        return imp(name, globals=globals, locals=locals, fromlist=fromlist, level=level)

    return wrap_importer_import


def load() -> None:
    """
    Find plugins and initialise the state.
    This must be called before any other functions in this module can be called.
    It can only be called once.
    """
    log.debug("Loading plugin manager")
    log.debug("Waiting for plugin lock")
    with _plugin_lock:
        log.debug("Acquired the plugin lock")

        builtins.__import__ = wrap_importer(builtins.__import__)
        scan_plugins()
        plugin_state = get_plugins_state()
        for plugin_uid, plugin_container in _plugins.items():
            if plugin_container.data.first_party or plugin_state.get(plugin_uid):
                _enable_plugin(plugin_uid)
        _plugin_diagnostic()

    log.debug("Finished loading plugins.")


def plugin_uids() -> tuple[LibraryUID, ...]:
    """Get a tuple of all plugin unique identifiers that are installed."""
    with _plugin_lock:
        return tuple(_plugins)


def get_plugins_state() -> dict[LibraryUID, bool]:
    """
    Get the state (enabled or disabled) for each plugin.
    If a plugin is not included it defaults to False.
    """
    # TODO: load this from the global and local configuration files
    return {}


def _set_plugin_state(
    plugin_container: PluginContainer, plugin_state: PluginState
) -> None:
    plugin_container.state = plugin_state
    uid = plugin_container.data.uid
    identifier = uid.identifier
    if plugin_state is PluginState.Enabled:
        if identifier in _enabled_plugins:
            raise RuntimeError(
                f"A plugin with identifier {identifier} has already been enabled."
            )
        _enabled_plugins[identifier] = uid
    elif identifier in _enabled_plugins:
        del _enabled_plugins[identifier]

    # self.__plugins_config[plugin_container.data.uid.to_string()] = bool(plugin_state)
    # self.__save_plugin_config()


def scan_plugins() -> None:
    """
    Scan the plugin directory for newly added plugins.
    This does not load the python code. It just parses the plugin.json file and populates the plugin entry.
    """
    with _plugin_lock:
        # Find and parse all plugins
        for manifest_path in glob.glob(
            os.path.join(
                glob.escape(first_party_plugin_directory()), "*", "*", "plugin.json"
            )
        ):
            try:
                plugin_path = os.path.dirname(manifest_path)
                plugin_container = PluginContainer.from_path(plugin_path)
                plugin_uid = plugin_container.data.uid

                if plugin_uid not in _plugins:
                    _plugins[plugin_uid] = plugin_container
                elif _plugins[plugin_uid].data.path != plugin_path:
                    log.warning(
                        f"Two plugins cannot have the same identifier and version.\n{_plugins[plugin_uid].data.path} and {plugin_path} have the same identifier and version."
                    )
            except Exception as e:
                log.exception(e)


def _has_library(requirement: Requirement) -> bool:
    try:
        return version(requirement.identifier) in requirement.specifier
    except Exception:
        return False


def _has_plugin(requirement: Requirement) -> bool:
    return (
        requirement.identifier in _enabled_plugins
        and _enabled_plugins[requirement.identifier] in requirement
    )


def _enable_plugin(plugin_uid: LibraryUID) -> None:
    """Enable a plugin. This must only be called by the main thread.
    :param plugin_uid: The unique identifier of the plugin to enable
    :raises: Exception if an error happened when loading the plugin.
    """
    with _plugin_lock:
        if not isinstance(plugin_uid, LibraryUID):
            raise TypeError
        plugin_container = _plugins[plugin_uid]
        if plugin_container.state is not PluginState.Disabled:
            # Cannot enable a plugin that is not currently disabled.
            return
        _set_plugin_state(plugin_container, PluginState.Inactive)

        enabled_count = -1
        while enabled_count:
            enabled_count = 0
            for plugin_container in list(_plugins.values()):
                if (
                    plugin_container.state is PluginState.Inactive
                    and PythonVersion in plugin_container.data.depends.python
                    and all(map(_has_library, plugin_container.data.depends.library))
                    and all(map(_has_plugin, plugin_container.data.depends.plugin))
                ):
                    # all dependencies are satisfied so the plugin can be enabled.
                    try:
                        _set_plugin_state(plugin_container, PluginState.Enabled)
                        log.debug(f"enabling plugin {plugin_container.data.uid}")
                        path = plugin_container.data.path
                        if os.path.isdir(path):
                            path = os.path.join(path, "__init__.py")

                        plugin_namespace, plugin_identifier = (
                            plugin_container.data.uid.identifier.split(".")
                        )

                        module_group_qualname = f"plugin.{plugin_namespace}"
                        if module_group_qualname not in sys.modules:
                            group_module = ModuleType(module_group_qualname)
                            group_module.__path__ = []
                            sys.modules[module_group_qualname] = group_module

                        module_qualname = (
                            f"plugin.{plugin_namespace}.{plugin_identifier}"
                        )
                        spec = spec_from_file_location(module_qualname, path)
                        if spec is None:
                            raise Exception
                        loader = spec.loader
                        if loader is None:
                            raise Exception
                        mod = module_from_spec(spec)
                        if mod is None:
                            raise Exception
                        sys.modules[module_qualname] = mod
                        loader.exec_module(mod)

                        plugin_container.module = mod

                        log.debug(f"enabled plugin {plugin_container.data.uid}")
                    except Exception as e:
                        log.exception(e)
                        display_exception(
                            title=f"Error while loading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                            error=str(e),
                            traceback=traceback.format_exc(),
                        )
                    else:
                        enabled_count += 1


def _plugin_diagnostic() -> None:
    """Useful plugin diagnostic data."""
    log.debug(f"Found {len(_plugins)} plugins.")
    for plugin_container in list(_plugins.values()):
        if plugin_container.state is PluginState.Enabled:
            log.debug(f"Plugin {plugin_container.data.uid} has been enabled.")
        elif plugin_container.state is PluginState.Disabled:
            log.debug(f"Plugin {plugin_container.data.uid} is not enabled.")
        elif plugin_container.state is PluginState.Inactive:
            log.debug(
                f"Plugin {plugin_container.data.uid} could not be enabled. "
                f"PyCompatible={PythonVersion in plugin_container.data.depends.python}, "
                f"MissingLibraries={[str(l) for l in plugin_container.data.depends.library if not _has_library(l)]}, "
                f"MissingPlugins={[str(p) for p in plugin_container.data.depends.plugin if not _has_plugin(p)]}"
            )


# def install_plugin(path: str):
#     """
#     Extract a zip file containing a plugin to the dynamic plugin directory and validate its contents.
#     This will not enable or execute any of the code.
#
#     :param path: The path to a zip file containing a plugin to install.
#     :raises Exception: if the file does not meet the requirements for a plugin.
#     """
#     if get_process_type() is ProcessType.Main:
#         raise NotImplementedError
#     else:
#         raise RuntimeError("The plugin state can only be modified in the main process.")
#
#
# def uninstall_plugin(plugin_uid: LibraryUID):
#     """
#     Disable and uninstall a plugin.
#
#     :param plugin_uid: The plugin uid to uninstall.
#     """
#     if get_process_type() is ProcessType.Main:
#         raise NotImplementedError
#     else:
#         raise RuntimeError("The plugin state can only be modified in the main process.")
