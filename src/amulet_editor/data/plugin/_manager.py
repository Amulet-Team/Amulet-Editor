from __future__ import annotations
from typing import NamedTuple, Optional
from threading import RLock
import os
import glob
import logging
import importlib
from queue import Queue
from enum import Enum

from PySide6.QtCore import QObject, Slot, QThread

from amulet_editor.data.process import ProcessType, get_process_type
from amulet_editor.data.process._messaging import register_global_function, call_in_parent, call_in_children
from amulet_editor.models.plugin import PluginUID, PluginData, Plugin
from amulet_editor.models.plugin._state import PluginState
from amulet_editor.models.plugin._requirement import PluginRequirement
from amulet_editor.models.plugin._container import PluginContainer
from ._modules import PluginDirs

log = logging.getLogger(__name__)

# A lock for the plugin state. Code must acquire this before touching the state
_plugin_lock = RLock()
# The plugin state
_plugins: dict[PluginUID, PluginContainer] = {}


class PluginJobType(Enum):
    Enable = 1
    Disable = 2
    Reload = 3


class PluginJob(NamedTuple):
    plugin_identifier: PluginUID
    job_type: PluginJobType


# A queue of jobs to apply to the plugins.
_plugin_queue: Queue = Queue()
# The thread to process plugin jobs.
_job_thread: Optional[PluginJobThread] = None


class PluginJobThread(QThread):
    def run(self):
        pass


def plugin_uids() -> tuple[PluginUID, ...]:
    """Get a tuple of all plugin unique identifiers that are installed."""
    return tuple(_plugins)


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


def scan_plugins():
    """
    Scan the plugin directory for newly added plugins.
    This does not load the python code. It just parses the plugin.json file populates the plugin entry.
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
                        if plugin_path != mod.__path__[0] if hasattr(mod, "__path__") else plugin_path != os.path.splitext(mod.__file__)[0]:
                            # If the path does not match the expected path then it shadows an existing module
                            log.warning(f"Skipping {plugin_container.data.path} because it would shadow module {plugin_uid.identifier}.")
                            continue

                    if plugin_uid not in _plugins:
                        _plugins[plugin_uid] = plugin_container
                    elif _plugins[plugin_uid].data.path != plugin_path:
                        log.warning(
                            f"Two plugins cannot have the same identifier and version.\n{_plugins[plugin_uid].data.path} and {plugin_path} have the same identifier and version."
                        )
                except Exception as e:
                    log.exception(e)


def get_plugin_state() -> dict[PluginUID, bool]:
    """
    Get the state (enabled or disabled) for each plugin.
    If a plugin is not included it defaults to False.
    """
    # TODO: load this from the global and local configuration files
    return {}


def init():
    """Find plugins and initialise the state."""
    with _plugin_lock:
        scan_plugins()
        plugin_state = get_plugin_state()
        for plugin_uid, plugin_container in _plugins.items():
            if plugin_state.get(plugin_uid) or plugin_container.data.locked:
                local_enable_plugin(plugin_uid)


def install_plugin(path: str):
    """
    Extract a zip file containing a plugin to the dynamic plugin directory and validate its contents.
    This will not enable or execute any of the code.

    :param path: The path to a zip file containing a plugin to install.
    :raises Exception: if the file does not meet the requirements for a plugin.
    """
    if get_process_type() is ProcessType.Main:
        raise NotImplementedError
    else:
        raise RuntimeError("The plugin state can only be modified in the main process.")


def uninstall_plugin(plugin_uid: PluginUID):
    """
    Disable and uninstall a plugin.

    :param plugin_uid: The plugin uid to uninstall.
    """
    if get_process_type() is ProcessType.Main:
        raise NotImplementedError
    else:
        raise RuntimeError("The plugin state can only be modified in the main process.")
