from __future__ import annotations

import inspect
import time
from typing import NamedTuple, Optional
from types import FrameType
from threading import RLock
import os
from os.path import normpath, samefile
import glob
import logging
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from importlib.metadata import version, packages_distributions
from queue import Queue, Empty
from enum import Enum
import sys
from collections import UserDict
import re
import traceback
import builtins

from packaging.version import Version

from PySide6.QtCore import QThread, Signal, QObject

from amulet_editor.application._splash import Splash
from amulet_editor.application._invoke import invoke

from amulet_editor.data.paths._plugin import (
    first_party_plugin_directory,
    third_party_plugin_directory,
)

# from amulet_editor.data.process._messaging import (
#     register_global_function,
#     call_in_parent,
#     call_in_children,
# )
from amulet_editor.models.plugin import LibraryUID
from amulet_editor.models.plugin._state import PluginState
from amulet_editor.models.plugin._container import PluginContainer
from amulet_editor.models.plugin._requirement import Requirement
from amulet_editor.models.widgets.traceback_dialog import display_exception


log = logging.getLogger(__name__)
PythonVersion = Version(".".join(map(str, sys.version_info[:3])))
Packages = packages_distributions()

"""
Notes:
First party plugins are stored in amulet_editor.plugins
They cannot be imported from that path because the __init__.py disallows it.
Third party plugins are imported as a zip and extracted to a writable directory with a UUID as the name.
Custom code loads the plugin package into sys.modules under its package name. Adding amulet_editor.plugins as sources root helps the IDE understand this.
TODO: look into generating stub files for the active plugins to help with development on the compiled version.
Plugins can import directly from other plugins to access static classes and functions 
"""


def plugin_dirs() -> tuple[str, str]:
    return first_party_plugin_directory(), third_party_plugin_directory()


class PluginJobType(Enum):
    Enable = 1
    Disable = 2
    Reload = 3


class PluginJob(NamedTuple):
    plugin_identifier: LibraryUID
    job_type: PluginJobType


# A lock for the plugin data. Code must acquire this before touching the plugin data
_plugin_lock = RLock()

# The plugin data
_plugins: dict[LibraryUID, PluginContainer] = {}

# A queue of jobs to apply to the plugins.
# Any function in this module can add jobs to this queue but only the job thread can remove items.
_plugin_queue: Queue = Queue()

# A map from the package identifier to the UID.
# Only plugins that are currently enabled will appear in this dictionary.
_enabled_plugins: dict[str, LibraryUID] = {}

_splash_load_screen: Optional[Splash] = None
_splash_unload_screen: Optional[Splash] = None


class PluginJobThread(QThread):
    def run(self):
        while True:
            job: Optional[PluginJob] = None
            while True:
                if self.isInterruptionRequested():
                    log.debug("Exiting plugin job thread")
                    return
                try:
                    job = _plugin_queue.get(timeout=0.1)
                except Empty:
                    continue
                else:
                    break
            if job.job_type is PluginJobType.Enable:
                _enable_plugin(job.plugin_identifier)
            elif job.job_type is PluginJobType.Disable:
                _disable_plugin(job.plugin_identifier)
            elif job.job_type is PluginJobType.Reload:
                _disable_plugin(job.plugin_identifier)
                _enable_plugin(job.plugin_identifier)


class Event(QObject):
    plugin_state_change = Signal(LibraryUID, PluginState)


_event = Event()


TracePattern = re.compile(r"\s*File\s*\"(?P<path>.*?)\"")


def get_trace_paths() -> list[str]:
    return list(
        reversed(
            [
                normpath(TracePattern.match(line).group("path"))
                for line in traceback.format_stack()
            ]
        )
    )[1:]


def _validate_import(imported_name: str, frame: FrameType):
    # Plugins can only import libraries and plugins they have specified as a dependency.
    # Plugins can only be imported by other plugins.
    # We step back through the stack.
    # If we find a plugin that does not have the authority then we raise an error.
    # If we do not find a plugin in the stack we raise an error

    # Get the root module name of the module being imported. Eg a.b.c => a
    imported_root_name = imported_name.split(".")[0]

    # Find what imported the module
    while frame.f_globals.get("__name__").split(".")[0] == "importlib":
        # Skip over the import mechanisms
        frame = frame.f_back

    if frame.f_globals.get("__name__") == __name__ and frame.f_code.co_name in {
        "_enable_plugin",
        "wrap_importer_import",
    }:
        return

    importer_name = frame.f_globals.get("__name__")
    if importer_name is None:
        raise RuntimeError(f"Could not find __name__ attribute for frame\n{frame}")

    importer_root_name = importer_name.split(".")[0]
    if importer_root_name in _enabled_plugins:
        # The module was imported by a plugin
        importer_uid = _enabled_plugins[importer_root_name]
        plugin_container = _plugins[importer_uid]
        if imported_root_name in _enabled_plugins:
            # A plugin imported a plugin
            if importer_root_name != imported_root_name:
                # a plugin imported a different plugin
                if not any(
                    dependency.identifier == imported_root_name
                    for dependency in plugin_container.data.depends.plugin
                ):
                    # imported by a plugin that does not have the dependency listed
                    raise RuntimeError(
                        f"Plugin {importer_root_name} imported plugin {imported_root_name} which it does not have authority for.\nYou must list a plugin dependency in your plugin's metadata to be able to import it."
                    )
        else:
            # A plugin imported a normal module
            if (
                imported_root_name in sys.builtin_module_names
                or imported_root_name in sys.stdlib_module_names
            ):
                # Plugins don't need to specify native python libraries.
                pass
            else:
                if imported_root_name not in Packages:
                    raise RuntimeError(f"Could not find library {importer_root_name}.")
                package_name = Packages[imported_root_name][0].lower().replace("-", "_")
                if not any(
                    dependency.identifier == package_name
                    for dependency in plugin_container.data.depends.library
                ):
                    raise RuntimeError(
                        f"Plugin {importer_root_name} imported library {imported_root_name} which it does not have authority for.\nYou must list a dependency in your plugin's metadata to be able to import it."
                    )
    elif imported_root_name in _enabled_plugins:
        code = frame.f_code
        raise RuntimeError(
            f"Plugin module {imported_name} was imported by a non-plugin module {importer_name} {getattr(code, 'co_qualname', None) or getattr(code, 'co_name', 'could not resolve function name')}"
        )


class CustomSysModules(UserDict):
    def __init__(self, original: dict):
        super().__init__()
        self.data = original  # I would prefer to do this but getitem does not get called if this line is used instead.
        # self.data = copy(original)

    def __getitem__(self, imported_name: str):
        if not isinstance(imported_name, str):
            raise TypeError

        # Find the first frame before UserDict code
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
            while frame.f_globals.get("__name__") == "collections.abc":
                frame = frame.f_back

            _validate_import(imported_name, frame)

        return super().__getitem__(imported_name)

    def _remove_plugin(self, plugin_name: str):
        plugin_prefix = f"{plugin_name}."
        key: str
        for key in list(self.data.keys()):
            if key == plugin_name or key.startswith(plugin_prefix):
                del self[key]


def wrap_importer(imp):
    def wrap_importer_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level:
            name_split = globals["__name__"].split(".")
            imported_name = f"{'.'.join(name_split[:len(name_split)-level+1])}.{name}"
        else:
            imported_name = name
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
            _validate_import(imported_name, frame)
        return imp(name, globals=globals, locals=locals, fromlist=fromlist, level=level)

    return wrap_importer_import


def load():
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

        sys.modules = CustomSysModules(sys.modules)
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


def unload():
    """
    Called just before application exit to tear down all plugins.
    :return:
    """
    global _splash_unload_screen

    log.debug("Unloading plugin manager")

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


def _set_plugin_state(plugin_container: PluginContainer, plugin_state: PluginState):
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


def scan_plugins():
    """
    Scan the plugin directory for newly added plugins.
    This does not load the python code. It just parses the plugin.json file and populates the plugin entry.
    """
    with _plugin_lock:
        # Find and parse all plugins
        for plugin_dir in plugin_dirs():
            for manifest_path in glob.glob(
                os.path.join(plugin_dir, "*", "plugin.json")
            ):
                try:
                    plugin_path = os.path.dirname(manifest_path)
                    plugin_container = PluginContainer.from_path(plugin_path)
                    plugin_uid = plugin_container.data.uid

                    # Ensure that the module name does not shadow an existing module
                    try:
                        mod = import_module(plugin_uid.identifier)
                    except ModuleNotFoundError:
                        # No module with this name. We are all good
                        pass
                    else:
                        # Imported a module with this name
                        if (
                            plugin_path != mod.__path__[0]
                            if hasattr(mod, "__path__")
                            else plugin_path != os.path.splitext(mod.__file__)[0]
                        ):
                            # If the path does not match the expected path then it shadows an existing module
                            log.warning(
                                f"Skipping {plugin_container.data.path} because it would shadow module {plugin_uid.identifier}."
                            )
                            continue

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


def _has_library(requirement: Requirement):
    try:
        return version(requirement.identifier) in requirement.specifier
    except Exception:
        return False


def _has_plugin(requirement: Requirement):
    return (
        requirement.identifier in _enabled_plugins
        and _enabled_plugins[requirement.identifier] in requirement
    )


def _enable_plugin(plugin_uid: LibraryUID):
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

                        spec = spec_from_file_location(
                            plugin_container.data.uid.identifier, path
                        )
                        if spec is None:
                            raise Exception
                        mod = module_from_spec(spec)
                        if mod is None:
                            raise Exception
                        sys.modules[plugin_container.data.uid.identifier] = mod
                        spec.loader.exec_module(mod)

                        plugin_container.instance = mod

                        try:
                            load_plugin = plugin_container.instance.load_plugin
                        except AttributeError:
                            # The plugin does not have a load_plugin method
                            pass
                        else:
                            # User code must be run from the main thread to avoid issues.
                            invoke(load_plugin)

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


def _plugin_diagnostic():
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


def _disable_plugin(plugin_uid: LibraryUID):
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


def _unload_plugin(plugin_container: PluginContainer):
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
    try:
        unload_plugin = plugin_container.instance.unload_plugin
    except AttributeError:
        # The plugin does not have an unload_plugin method
        pass
    else:
        # User code must be run from the main thread to avoid issues.
        try:
            invoke(unload_plugin)
        except Exception as e:
            log.exception(e)
            display_exception(
                title=f"Error while unloading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                error=str(e),
                traceback=traceback.format_exc(),
            )
    plugin_container.instance = None

    # Remove the module from sys.modules
    modules = sys.modules
    if isinstance(modules, CustomSysModules):
        modules._remove_plugin(plugin_container.data.uid.identifier)


def _recursive_inactive_plugins(plugin_uid: LibraryUID):
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
