from __future__ import annotations

from typing import NamedTuple, Optional
from threading import RLock
import os
from os.path import relpath, normpath, dirname
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

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QApplication

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
from amulet_editor.application._invoke import invoke


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


class CustomDict(UserDict):
    def __init__(self, original: dict):
        super().__init__()
        # self.data = original  # I would prefer to do this but getitem does not get called if this line is used instead.
        self.data = copy(original)

    # def __getitem__(self, key):
    #     mod = super().__getitem__(key)
    #     try:
    #         if mod.__file__ is None:
    #             # Namespace package does not have a file
    #             raise AttributeError
    #
    #         module_path = normpath(mod.__file__)
    #         # Find the plugin directory this module is from (if any)
    #         plugin_dir = next(filter(lambda path: module_path != path and module_path.startswith(path), PluginDirs), None)
    #     except AttributeError:
    #         pass
    #     else:
    #         if plugin_dir is not None:
    #             plugin_dir = normpath(plugin_dir)
    #             plugin_path = os.path.join(
    #                 plugin_dir, relpath(module_path, plugin_dir).split(os.sep)[0]
    #             )
    #             for frame in get_trace_paths()[2:]:
    #                 if frame.startswith(plugin_path):
    #                     break
    #                 elif any(map(frame.startswith, PluginDirs)):
    #                     raise ImportError(
    #                         "Plugins cannot directly import other plugins. You must use the plugin API to interact with other plugins.\n"
    #                         f"Plugin {frame} tried to import {key}"
    #                     )
    #     return mod


def load():
    """
    Find plugins and initialise the state.
    This must be called before any other functions in this module can be called.
    It can only be called once.
    """
    with _plugin_lock:
        if _job_thread.isRunning():
            raise RuntimeError("Plugin manager has already been initialised.")
        sys.modules = CustomDict(sys.modules)
        scan_plugins()
        plugin_state = get_plugins_state()
        for plugin_uid, plugin_container in _plugins.items():
            if plugin_state.get(plugin_uid) or plugin_container.data.locked:
                local_enable_plugin(plugin_uid)
        _job_thread.start()


def unload():
    """
    Called just before application exit to tear down all plugins.
    :return:
    """
    # Shut down the job thread so that it cannot process anything
    _job_thread.requestInterruption()
    _job_thread.wait()

    with _plugin_lock:
        for plugin_uid in _plugins.keys():
            _disable_plugin(plugin_uid)


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
                        log.debug(f"enabling plugin {plugin_container.data.uid}")
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

                        _set_plugin_state(plugin_container, PluginState.Enabled)
                        log.debug(f"enabled plugin {plugin_container.data.uid}")
                    except Exception as e:
                        log.exception(e)
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
    plugin_container.instance = None
    sys.modules.pop(plugin_container.data.uid.identifier, None)
    # TODO: remove all submodules


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
