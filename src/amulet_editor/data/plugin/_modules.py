"""Modify sys.modules to disallow importing plugins directly."""

from __future__ import annotations

import logging
import os.path
from os.path import relpath, normpath
from typing import List
import sys
import traceback
import re
from collections import UserDict
from copy import copy

import amulet_editor
from amulet_editor.data.paths._plugin import plugin_directory


log = logging.getLogger(__name__)

FirstPartyPluginDir = os.path.abspath(
    os.path.join(amulet_editor.__path__[0], "plugins")
)
ThirdPartyPluginDir = os.path.abspath(plugin_directory())
PluginDirs = (FirstPartyPluginDir, ThirdPartyPluginDir)

TracePattern = re.compile(r"\s*File\s*\"(?P<path>.*?)\"")


def get_trace_paths() -> List[str]:
    return list(reversed([normpath(TracePattern.match(line).group("path")) for line in traceback.format_stack()]))[1:]


class CustomDict(UserDict):
    def __init__(self, original: dict):
        super().__init__()
        # self.data = original  # I would prefer to do this but getitem does not get called if this line is used instead.
        self.data = copy(original)

    def __getitem__(self, key):
        mod = super().__getitem__(key)
        try:
            module_path = normpath(mod.__file__)
            plugin_dir = next(filter(module_path.startswith, PluginDirs), None)
        except AttributeError:
            pass
        else:
            if plugin_dir is not None:
                plugin_dir = normpath(plugin_dir)
                plugin_path = os.path.join(plugin_dir, relpath(module_path, plugin_dir).split(os.sep)[0])
                for frame in get_trace_paths()[2:]:
                    if frame.startswith(plugin_path):
                        break
                    elif any(map(frame.startswith, PluginDirs)):
                        raise ImportError(
                            "Plugins cannot directly import other plugins. You must use the plugin API to interact with other plugins.\n"
                            f"Plugin {frame} tried to import {key}"
                        )
        return mod


sys.modules = CustomDict(sys.modules)
