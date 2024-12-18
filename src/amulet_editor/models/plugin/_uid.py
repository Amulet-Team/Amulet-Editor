from __future__ import annotations

import re
from typing import Any

from packaging.version import Version
from runtime_final import final


@final
class LibraryUID:
    """A named tuple containing an identifier for a library/plugin and a version number."""

    def __init__(self, identifier: str, version: Version):
        self._identifier = identifier.lower().replace("-", "_")
        self._version = version

    def __repr__(self) -> str:
        return f"LibraryUID({self._identifier!r}, {self._version!r})"

    def __str__(self) -> str:
        return f"{self._identifier} {self._version}"

    def __hash__(self) -> int:
        return hash((self._identifier, self._version))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LibraryUID):
            return NotImplemented
        return self._identifier == other._identifier and self._version == other._version

    @property
    def identifier(self) -> str:
        """The package name. This is the name used when importing the package. Eg "my_name_my_plugin_v1". This must be a valid python identifier."""
        return self._identifier

    @property
    def version(self) -> Version:
        """The version number of the plugin."""
        return self._version

    def to_string(self) -> str:
        return f"{self.identifier}@{self.version}"

    @classmethod
    def from_string(cls, s: str) -> LibraryUID:
        match = re.fullmatch(r"(?P<identifier>[a-zA-Z_]+\w*)@(?P<version>.*)", s)
        if match is None:
            raise ValueError(f"Invalid LibraryUID string: {s}")
        version = Version(match.group("version"))
        return cls(match.group("identifier"), version)
