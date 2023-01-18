from __future__ import annotations

from typing import NamedTuple
import re
from packaging.specifiers import SpecifierSet

from ._uid import PluginUID


RequirementPattern = re.compile(
    r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)(?P<requirement>.*)"
)


class PluginRequirement(NamedTuple):
    plugin_identifier: str  # The package name
    specifier: SpecifierSet  # The version specifier. It is recommended to use the compatible format. Eg. "~=1.0"

    @classmethod
    def from_string(cls, requirement: str):
        match = RequirementPattern.fullmatch(requirement)
        if match is None:
            raise ValueError(
                f'"{requirement}" is not a valid requirement.\n It must be a python identifier followed by an optional PEP 440 compatible version specifier'
            )
        specifier = SpecifierSet(match.group("requirement"))
        return cls(match.group("identifier"), specifier)

    def __contains__(self, item: PluginUID):
        if not isinstance(item, PluginUID):
            raise TypeError
        return (
            item.identifier == self.plugin_identifier and item.version in self.specifier
        )
