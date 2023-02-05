from __future__ import annotations

from typing import NamedTuple
import re
from packaging.specifiers import SpecifierSet

from ._uid import LibraryUID


RequirementPattern = re.compile(
    r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)(?P<requirement>.*)"
)


class Requirement(NamedTuple):
    identifier: str  # The package name
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

    def __contains__(self, item: LibraryUID):
        if not isinstance(item, LibraryUID):
            raise TypeError
        return item.identifier == self.identifier and item.version in self.specifier
