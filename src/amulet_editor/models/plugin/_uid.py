from __future__ import annotations

from typing import NamedTuple
import re

from packaging.version import Version
from runtime_final import final


@final
class PluginUID(NamedTuple):
    identifier: str  # The package name. This is the name used when importing the package. Eg "my_name_my_plugin_v1". This must be a valid python identifier.
    version: Version  # The version number of the plugin.

    def to_string(self):
        return f"{self.identifier}@{self.version}"

    @classmethod
    def from_string(cls, s: str):
        match = re.fullmatch(r"(?P<identifier>[a-zA-Z_]+\w*)@(?P<version>.*)", s)
        if match is None:
            raise ValueError(f"Invalid PluginUID string: {s}")
        version = Version(match.group("version"))
        return cls(match.group("identifier"), version)
