from __future__ import annotations

import re
from packaging.specifiers import SpecifierSet

from ._uid import LibraryUID


RequirementPattern = re.compile(
    r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)(?P<requirement>.*)"
)


class Requirement:
    def __init__(self, identifier: str, specifier: SpecifierSet):
        self._identifier = identifier.lower().replace("-", "_")
        self._specifier = specifier

    @property
    def identifier(self) -> str:
        """The package name"""
        return self._identifier

    @property
    def specifier(self) -> SpecifierSet:
        """The version specifier. It is recommended to use the compatible format. Eg. "~=1.0"""
        return self._specifier

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

    def __str__(self):
        return f"{self.identifier}{self.specifier}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.identifier!r}, {self.specifier!r})"
