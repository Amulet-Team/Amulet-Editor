from __future__ import annotations

import inspect
import time
from typing import NamedTuple, Optional, Protocol
from types import FrameType, ModuleType
from threading import RLock
import os
from os.path import samefile
import glob
import logging
import gc
from importlib.util import spec_from_file_location, module_from_spec
from importlib.metadata import version, packages_distributions

# from queue import Queue
from enum import Enum
import sys
from collections import UserDict
from collections.abc import Mapping, Sequence
import traceback
import builtins

from packaging.version import Version

from PySide6.QtCore import Signal, QObject

from amulet.app._splash import Splash
from amulet.app.invoke import invoke

from amulet.app.path._plugin import plugin_dirs

# from amulet.app.data.process._messaging import (
#     register_global_function,
#     call_in_parent,
#     call_in_children,
# )
from ._uid import LibraryUID
from ._plugin import PluginV1
from ._state import PluginState
from ._container import PluginContainer
from ._requirement import Requirement
from amulet.app.exception import display_exception
from amulet.app._sys import set_sys_modules

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
First party plugins are stored in builtin_plugins
Third party plugins are imported as a zip and extracted to a writable directory with a UUID as the name.
Custom code loads the plugin package into sys.modules under its package name. Adding builtin_plugins as sources root helps the IDE understand this.
TODO: look into generating stub files for the active plugins to help with development on the compiled version.
Plugins can import directly from other plugins to access static classes and functions 
"""


class PluginJobType(Enum):
    Enable = 1
    Disable = 2
    Reload = 3


# class PluginJob(NamedTuple):
#     plugin_identifier: LibraryUID
#     job_type: PluginJobType


# A lock for the plugin data. Code must acquire this before touching the plugin data
_plugin_lock = RLock()

# The plugin data
_plugins: dict[LibraryUID, PluginContainer] = {}

# A queue of jobs to apply to the plugins.
# Any function in this module can add jobs to this queue but only the job thread can remove items.
# _plugin_queue: Queue = Queue()

# A map from the package identifier to the UID.
# Only plugins that are currently enabled will appear in this dictionary.
_enabled_plugins: dict[str, LibraryUID] = {}

_splash_load_screen: Optional[Splash] = None
_splash_unload_screen: Optional[Splash] = None


class Event(QObject):
    plugin_state_change = Signal(LibraryUID, PluginState)


_event = Event()


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


class CustomSysModules(UserDict[str, ModuleType]):
    def __init__(self, original: dict) -> None:
        super().__init__()
        self.data = original

    def __getitem__(self, imported_name: str) -> ModuleType:
        if not isinstance(imported_name, str):
            raise TypeError

        # Find the first frame before UserDict code
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
            while frame is not None and frame.f_globals.get("__name__") in {
                "collections",
                "collections.abc",
                "inspect",
                "dataclasses",
            }:
                frame = frame.f_back
            _validate_import(imported_name, frame)

        return super().__getitem__(imported_name)


class ImportProtocol(Protocol):
    def __call__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType: ...


def wrap_importer(imp: ImportProtocol) -> ImportProtocol:
    def wrap_importer_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
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
    global _splash_load_screen
    log.debug("Loading plugin manager")
    log.debug("Waiting for plugin lock")
    with _plugin_lock:
        log.debug("Acquired the plugin lock")

        _splash_load_screen = Splash()
        _splash_load_screen.setModal(True)
        _splash_load_screen.show()

        # Remove the plugin directories from sys.path so that they are not directly importable
        for i in range(len(sys.path) - 1, -1, -1):
            path = sys.path[i]
            for plugin_path in plugin_dirs():
                try:
                    is_same = samefile(path, plugin_path)
                except FileNotFoundError:
                    pass
                else:
                    if is_same:
                        sys.path.pop(i)
                        break

        # Disable importing from builtin_plugins
        sys.modules["builtin_plugins"] = None  # type: ignore
        plugin_module = ModuleType("plugin")
        plugin_module.__path__ = []
        sys.modules["plugin"] = plugin_module

        set_sys_modules(CustomSysModules(sys.modules))
        builtins.__import__ = wrap_importer(builtins.__import__)
        scan_plugins()
        plugin_state = get_plugins_state()
        for plugin_uid, plugin_container in _plugins.items():
            if plugin_state.get(plugin_uid) or plugin_container.data.locked:
                _enable_plugin(plugin_uid)
        _plugin_diagnostic()

        _splash_load_screen.close()
        _splash_load_screen = None

    log.debug("Finished loading plugins.")


def unload() -> None:
    """
    Called just before application exit to tear down all plugins.
    :return:
    """
    global _splash_unload_screen

    gc.collect()

    log.debug("Unloading plugins")

    log.debug("Waiting for plugin lock")
    with _plugin_lock:
        log.debug("Acquired the plugin lock")

        _splash_unload_screen = Splash()
        _splash_unload_screen.setModal(True)
        _splash_unload_screen.show()

        t = time.time()

        for plugin_uid in _plugins.keys():
            _disable_plugin(plugin_uid)

        sleep_time = 0.5 - (time.time() - t)
        if sleep_time > 0:
            time.sleep(sleep_time)
        _splash_unload_screen.close()
        _splash_unload_screen = None

    gc.collect()

    log.debug("Finished unloading plugins")


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
    _event.plugin_state_change.emit(plugin_container.data.uid, plugin_container.state)


def scan_plugins() -> None:
    """
    Scan the plugin directory for newly added plugins.
    This does not load the python code. It just parses the plugin.json file and populates the plugin entry.
    """
    with _plugin_lock:
        # Find and parse all plugins
        for plugin_dir in plugin_dirs():
            for manifest_path in glob.glob(
                os.path.join(glob.escape(plugin_dir), "plugin", "*", "*", "plugin.json")
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


# @register_global_function
# def local_enable_plugin(plugin_uid: LibraryUID):
#     """
#     Load and initialise a plugin in the current processes.
#     Any plugins that are inactive because they depend on this plugin will also be enabled.
#     This returns immediately and is completed asynchronously.
#
#     :param plugin_uid: The plugin uid to load.
#     """
#     log.debug(f"Locally enabling plugin {plugin_uid}")
#     _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Enable))


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
    """Enable a plugin. This must only be called by the job thread.
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
                        if _splash_load_screen is not None:
                            _splash_load_screen.showMessage(
                                f"Enabling plugin {plugin_container.data.uid.identifier}"
                            )
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

                        try:
                            plugin = plugin_container.module.plugin
                        except AttributeError:
                            # The plugin does not have a plugin attribute
                            plugin = PluginV1()

                        if not isinstance(plugin, PluginV1):
                            raise ValueError(
                                "Plugin attribute must be an instance of amulet.app.plugin.PluginV1"
                            )
                        plugin_container.plugin = plugin
                        # User code must be run from the main thread to avoid issues.
                        invoke(plugin_container.plugin.load)

                        log.debug(f"enabled plugin {plugin_container.data.uid}")
                    except Exception as e:
                        log.exception(e)
                        display_exception(
                            title=f"Error while loading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                            error=str(e),
                            traceback=traceback.format_exc(),
                        )

                        # Since the plugin failed to load we must try and disable it
                        _disable_plugin(plugin_container.data.uid)
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


# @register_global_function
# def local_disable_plugin(plugin_uid: LibraryUID):
#     """
#     Disable and destroy a plugin in the current process.
#     Any dependent plugins will be disabled before disabling this plugin.
#     This returns immediately and is completed asynchronously.
#
#     :param plugin_uid: The plugin uid to disable.
#     """
#     log.debug(f"Locally disabling plugin {plugin_uid}")
#     _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Disable))


def _disable_plugin(plugin_uid: LibraryUID) -> None:
    """Disable a plugin and inactive all dependents. This must only be called by the job thread."""
    with _plugin_lock:
        if not isinstance(plugin_uid, LibraryUID):
            raise TypeError
        plugin_container = _plugins[plugin_uid]
        if plugin_container.state is PluginState.Disabled:
            # Cannot disable a plugin that is already disabled
            return
        elif plugin_container.state is PluginState.Enabled:
            _unload_plugin(plugin_container)
        _set_plugin_state(plugin_container, PluginState.Disabled)


def _unload_plugin(plugin_container: PluginContainer) -> None:
    """Unload and destroy a plugin. This must only be called by the job thread."""
    _recursive_inactive_plugins(plugin_container.data.uid)
    if _splash_load_screen is not None:
        _splash_load_screen.showMessage(
            f"Disabling plugin {plugin_container.data.uid.identifier}"
        )
    elif _splash_unload_screen is not None:
        _splash_unload_screen.showMessage(
            f"Disabling plugin {plugin_container.data.uid.identifier}"
        )

    if plugin_container.plugin is not None:
        try:
            # User code must be run from the main thread to avoid issues.
            invoke(plugin_container.plugin.unload)
        except Exception as e:
            log.exception(e)
            display_exception(
                title=f"Error while unloading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                error=str(e),
                traceback=traceback.format_exc(),
            )
    plugin_container.module = None
    plugin_container.plugin = None

    # Remove the module from sys.modules
    modules = sys.modules
    if isinstance(modules, CustomSysModules):
        module_qualname = f"plugin.{plugin_container.data.uid.identifier}"
        plugin_prefix = f"{module_qualname}."
        for key in list(modules.keys()):
            if key == module_qualname or key.startswith(plugin_prefix):
                del modules[key]


def _recursive_inactive_plugins(plugin_uid: LibraryUID) -> None:
    """
    Recursively inactive all dependents of a plugin This must only be called by the job thread.
    When a plugin is disabled none of its dependents are valid any more so they must be inactivated.
    :param plugin_uid: The plugin unique identifier to find dependents of.
    """
    for plugin_container in _plugins.values():
        if plugin_container.state is PluginState.Enabled and any(
            plugin_uid in requirement
            for requirement in plugin_container.data.depends.plugin
        ):
            _unload_plugin(plugin_container)
            _set_plugin_state(plugin_container, PluginState.Inactive)


# @register_global_function
# def local_reload_plugin(plugin_uid: LibraryUID):
#     """
#     Disable a plugin if enabled and reload from source.
#     Only effects the current process.
#     This returns immediately and is completed asynchronously.
#
#     :param plugin_uid: The plugin uid to reload.
#     """
#     log.debug(f"Locally reloading plugin {plugin_uid}")
#     _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Reload))


# @register_global_function
# def global_enable_plugin(plugin_uid: LibraryUID):
#     """
#     Enable a plugin for all processes.
#     This returns immediately and is completed asynchronously.
#     """
#     log.debug(f"Globally enabling plugin {plugin_uid}")
#     if get_process_type() is ProcessType.Main:
#         # If this is the main process enable for self
#         # and tell all child processes to enable
#         local_enable_plugin(plugin_uid)
#         call_in_children(local_enable_plugin, plugin_uid)
#     elif get_process_type() is ProcessType.Child:
#         # If this is a child process then notify the main process.
#         call_in_parent(global_enable_plugin, plugin_uid)
#     else:
#         raise RuntimeError


# @register_global_function
# def global_disable_plugin(plugin_uid: LibraryUID):
#     """
#     Disable a plugin for all processes.
#     This returns immediately and is completed asynchronously.
#     """
#     log.debug(f"Globally disabling plugin {plugin_uid}")
#     if get_process_type() is ProcessType.Main:
#         # If this is the main process enable for self
#         # and tell all child processes to enable
#         local_disable_plugin(plugin_uid)
#         call_in_children(local_disable_plugin, plugin_uid)
#     elif get_process_type() is ProcessType.Child:
#         # If this is a child process then notify the main process.
#         call_in_parent(global_disable_plugin, plugin_uid)
#     else:
#         raise RuntimeError


# @register_global_function
# def global_reload_plugin(plugin_uid: LibraryUID):
#     """
#     Reload a plugin for all processes.
#     This returns immediately and is completed asynchronously.
#     """
#     log.debug(f"Globally reloading plugin {plugin_uid}")
#     if get_process_type() is ProcessType.Main:
#         # If this is the main process enable for self
#         # and tell all child processes to enable
#         local_reload_plugin(plugin_uid)
#         call_in_children(local_reload_plugin, plugin_uid)
#     elif get_process_type() is ProcessType.Child:
#         # If this is a child process then notify the main process.
#         call_in_parent(global_reload_plugin, plugin_uid)
#     else:
#         raise RuntimeError


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
