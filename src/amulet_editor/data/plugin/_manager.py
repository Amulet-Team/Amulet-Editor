from __future__ import annotations

import inspect
import time
from typing import NamedTuple, Optional
from threading import RLock
import os
from os.path import relpath, normpath, dirname, samefile
import glob
import logging
import importlib
from queue import Queue, Empty
from enum import Enum
import sys
from collections import UserDict
import re
import traceback
from copy import copy

from PySide6.QtCore import QThread, Signal, QObject, QTimer, QCoreApplication

from amulet_editor.application._splash import Splash
from amulet_editor.application._invoke import invoke

from amulet_editor.data.paths._plugin import (
    first_party_plugin_directory,
    third_party_plugin_directory,
)
from amulet_editor.data.process import ProcessType, get_process_type
from amulet_editor.data.process._messaging import (
    register_global_function,
    call_in_parent,
    call_in_children,
)
from amulet_editor.models.plugin import PluginUID, PluginData
from amulet_editor.models.plugin._state import PluginState
from amulet_editor.models.plugin._requirement import PluginRequirement
from amulet_editor.models.plugin._container import PluginContainer
from amulet_editor.models.widgets import TracebackDialog


log = logging.getLogger(__name__)


"""
Notes:
First party plugins are stored in amulet_editor.plugins
They cannot be imported from that path because the __init__.py disallows it.
Third party plugins are imported as a zip and extracted to a writable directory with a UUID as the name.
Custom code loads the plugin package into sys.modules under its package name. Adding amulet_editor.plugins as sources root helps the IDE understand this.
TODO: look into generating stub files for the active plugins to help with development on the compiled version.
Plugins can import directly from other plugins to access static classes and functions 
"""

PluginDirs = [first_party_plugin_directory(), third_party_plugin_directory()]


class PluginJobType(Enum):
    Enable = 1
    Disable = 2
    Reload = 3


class PluginJob(NamedTuple):
    plugin_identifier: PluginUID
    job_type: PluginJobType


# A lock for the plugin data. Code must acquire this before touching the plugin data
_plugin_lock = RLock()

# The plugin data
_plugins: dict[PluginUID, PluginContainer] = {}

# A queue of jobs to apply to the plugins.
# Any function in this module can add jobs to this queue but only the job thread can remove items.
_plugin_queue: Queue = Queue()

# A map from the package identifier to the UID.
# Only plugins that are currently enabled will appear in this dictionary.
_enabled_plugins: dict[str, PluginUID] = {}

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
    plugin_state_change = Signal(PluginUID, PluginState)


# The thread to process plugin jobs.
_job_thread: Optional[PluginJobThread] = PluginJobThread()

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


class CustomSysModules(UserDict):
    def __init__(self, original: dict):
        super().__init__()
        # self.data = original  # I would prefer to do this but getitem does not get called if this line is used instead.
        self.data = copy(original)

    def __getitem__(self, imported_name: str):
        if not isinstance(imported_name, str):
            raise TypeError

        # Plugins can only be imported by other plugins that have the dependency listed.
        # We step back through the stack.
        # If we find a plugin that does not have the authority then we raise an error.
        # If we do not find a plugin in the stack we raise an error

        # Get the root module name of the module being imported. Eg a.b.c => a
        imported_root_name = imported_name.split(".")[0]
        # If the imported module is an enabled plugin
        if imported_root_name in _enabled_plugins:
            # Find what imported it
            frame = inspect.currentframe().f_back
            while frame:
                importer_name = frame.f_globals.get("__name__")
                if importer_name is None:
                    raise RuntimeError(f"Could not find __name__ attribute for frame\n{frame}")
                importer_root_name = importer_name.split(".")[0]

                if importer_root_name in _enabled_plugins:
                    # We found the plugin that imported the plugin module

                    if importer_root_name == imported_root_name:
                        # imported by itself
                        break

                    importer_uid = _enabled_plugins[importer_root_name]
                    plugin_container = _plugins[importer_uid]
                    if any(dependency.plugin_identifier == imported_root_name for dependency in plugin_container.data.depends):
                        # imported by a plugin that has the dependency listed
                        break

                    raise RuntimeError(f"Plugin {importer_root_name} imported plugin {imported_root_name} which it does not have authority for.\nYou must list a plugin dependency to be able to import it.")

                frame = frame.f_back

            else:
                raise RuntimeError(f"Plugin module {imported_name} was imported by a non-plugin module")

        return super().__getitem__(imported_name)

    def _remove_plugin(self, plugin_name: str):
        plugin_prefix = f"{plugin_name}."
        key: str
        for key in list(self.data.keys()):
            if key == plugin_name or key.startswith(plugin_prefix):
                del self[key]


def load():
    """
    Find plugins and initialise the state.
    This must be called before any other functions in this module can be called.
    It can only be called once.
    """
    global _splash_load_screen
    log.debug("Loading plugin manager")
    if _job_thread.isRunning():
        raise RuntimeError("Plugin manager has already been initialised.")
    log.debug("Waiting for plugin lock")
    with _plugin_lock:
        log.debug("Acquired the plugin lock")

        _splash_load_screen = Splash()
        _splash_load_screen.setModal(True)
        _splash_load_screen.show()

        # Remove the plugin directories from sys.path so that they are not directly importable
        for i in range(len(sys.path)-1, -1, -1):
            path = sys.path[i]
            for plugin_path in PluginDirs:
                try:
                    is_same = samefile(path, plugin_path)
                except FileNotFoundError:
                    pass
                else:
                    if is_same:
                        sys.path.pop(i)
                        break

        sys.modules = CustomSysModules(sys.modules)
        scan_plugins()
        plugin_state = get_plugins_state()
        for plugin_uid, plugin_container in _plugins.items():
            if plugin_state.get(plugin_uid) or plugin_container.data.locked:
                _enable_plugin(plugin_uid)
        _job_thread.start()

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

    # Shut down the job thread so that it cannot process anything
    log.debug("Waiting for the plugin job thread to finish")
    _job_thread.requestInterruption()
    _job_thread.wait()
    log.debug("Plugin job thread finished")

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


def plugin_uids() -> tuple[PluginUID, ...]:
    """Get a tuple of all plugin unique identifiers that are installed."""
    with _plugin_lock:
        return tuple(_plugins)


def get_plugins_state() -> dict[PluginUID, bool]:
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
            raise RuntimeError(f"A plugin with identifier {identifier} has already been enabled.")
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
        for plugin_dir in PluginDirs:
            for manifest_path in glob.glob(
                os.path.join(plugin_dir, "*", "plugin.json")
            ):
                try:
                    plugin_path = os.path.dirname(manifest_path)
                    plugin_container = PluginContainer.from_path(plugin_path)
                    plugin_uid = plugin_container.data.uid

                    # Ensure that the module name does not shadow an existing module
                    try:
                        mod = importlib.import_module(plugin_uid.identifier)
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


@register_global_function
def local_enable_plugin(plugin_uid: PluginUID):
    """
    Load and initialise a plugin in the current processes.
    Any plugins that are inactive because they depend on this plugin will also be enabled.
    This returns immediately and is completed asynchronously.

    :param plugin_uid: The plugin uid to load.
    """
    log.debug(f"Locally enabling plugin {plugin_uid}")
    _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Enable))


def _enable_plugin(plugin_uid: PluginUID):
    """Enable a plugin. This must only be called by the job thread.
    :param plugin_uid: The unique identifier of the plugin to enable
    :raises: Exception if an error happened when loading the plugin.
    """
    with _plugin_lock:
        if not isinstance(plugin_uid, PluginUID):
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
                if plugin_container.state is PluginState.Inactive and all(
                    any(
                        uid in requirement and plugin.state is PluginState.Enabled
                        for uid, plugin in _plugins.items()
                    )
                    for requirement in plugin_container.data.depends
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

                        spec = importlib.util.spec_from_file_location(
                            plugin_container.data.uid.identifier, path
                        )
                        if spec is None:
                            raise Exception
                        mod = importlib.util.module_from_spec(spec)
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
                        dialog = TracebackDialog(
                            title=f"Error while loading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                            error=str(e),
                            traceback=traceback.format_exc(),
                        )
                        dialog.exec()

                        # Since the plugin failed to load we must try and disable it
                        _disable_plugin(plugin_container.data.uid)
                    else:
                        enabled_count += 1


@register_global_function
def local_disable_plugin(plugin_uid: PluginUID):
    """
    Disable and destroy a plugin in the current process.
    Any dependent plugins will be disabled before disabling this plugin.
    This returns immediately and is completed asynchronously.

    :param plugin_uid: The plugin uid to disable.
    """
    log.debug(f"Locally disabling plugin {plugin_uid}")
    _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Disable))


def _disable_plugin(plugin_uid: PluginUID):
    """Disable a plugin and inactive all dependents. This must only be called by the job thread."""
    with _plugin_lock:
        if not isinstance(plugin_uid, PluginUID):
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
            dialog = TracebackDialog(
                title=f"Error while unloading plugin {plugin_container.data.uid.identifier} {plugin_container.data.uid.version}",
                error=str(e),
                traceback=traceback.format_exc(),
            )
            dialog.exec()
    plugin_container.instance = None

    # Remove the module from sys.modules
    modules = sys.modules
    if isinstance(modules, CustomSysModules):
        modules._remove_plugin(plugin_container.data.uid.identifier)


def _recursive_inactive_plugins(plugin_uid: PluginUID):
    """
    Recursively inactive all dependents of a plugin This must only be called by the job thread.
    When a plugin is disabled none of its dependents are valid any more so they must be inactivated.
    :param plugin_uid: The plugin unique identifier to find dependents of.
    """
    for plugin_container in _plugins.values():
        if plugin_container.state is PluginState.Enabled and any(
            plugin_uid in requirement for requirement in plugin_container.data.depends
        ):
            _unload_plugin(plugin_container)
            _set_plugin_state(plugin_container, PluginState.Inactive)


@register_global_function
def local_reload_plugin(plugin_uid: PluginUID):
    """
    Disable a plugin if enabled and reload from source.
    Only effects the current process.
    This returns immediately and is completed asynchronously.

    :param plugin_uid: The plugin uid to reload.
    """
    log.debug(f"Locally reloading plugin {plugin_uid}")
    _plugin_queue.put(PluginJob(plugin_uid, PluginJobType.Reload))


@register_global_function
def global_enable_plugin(plugin_uid: PluginUID):
    """
    Enable a plugin for all processes.
    This returns immediately and is completed asynchronously.
    """
    log.debug(f"Globally enabling plugin {plugin_uid}")
    if get_process_type() is ProcessType.Main:
        # If this is the main process enable for self
        # and tell all child processes to enable
        local_enable_plugin(plugin_uid)
        call_in_children(local_enable_plugin, plugin_uid)
    elif get_process_type() is ProcessType.Child:
        # If this is a child process then notify the main process.
        call_in_parent(global_enable_plugin, plugin_uid)
    else:
        raise RuntimeError


@register_global_function
def global_disable_plugin(plugin_uid: PluginUID):
    """
    Disable a plugin for all processes.
    This returns immediately and is completed asynchronously.
    """
    log.debug(f"Globally disabling plugin {plugin_uid}")
    if get_process_type() is ProcessType.Main:
        # If this is the main process enable for self
        # and tell all child processes to enable
        local_disable_plugin(plugin_uid)
        call_in_children(local_disable_plugin, plugin_uid)
    elif get_process_type() is ProcessType.Child:
        # If this is a child process then notify the main process.
        call_in_parent(global_disable_plugin, plugin_uid)
    else:
        raise RuntimeError


@register_global_function
def global_reload_plugin(plugin_uid: PluginUID):
    """
    Reload a plugin for all processes.
    This returns immediately and is completed asynchronously.
    """
    log.debug(f"Globally reloading plugin {plugin_uid}")
    if get_process_type() is ProcessType.Main:
        # If this is the main process enable for self
        # and tell all child processes to enable
        local_reload_plugin(plugin_uid)
        call_in_children(local_reload_plugin, plugin_uid)
    elif get_process_type() is ProcessType.Child:
        # If this is a child process then notify the main process.
        call_in_parent(global_reload_plugin, plugin_uid)
    else:
        raise RuntimeError


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
# def uninstall_plugin(plugin_uid: PluginUID):
#     """
#     Disable and uninstall a plugin.
#
#     :param plugin_uid: The plugin uid to uninstall.
#     """
#     if get_process_type() is ProcessType.Main:
#         raise NotImplementedError
#     else:
#         raise RuntimeError("The plugin state can only be modified in the main process.")
