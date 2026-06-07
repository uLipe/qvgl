from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Loc:
    line: int = 1
    column: int = 1


@dataclass
class Import:
    module: str
    version: str
    loc: Loc = field(default_factory=Loc)

    @property
    def key(self) -> str:
        return f"{self.module} {self.version}"


@dataclass
class Object:
    type_name: str
    loc: Loc = field(default_factory=Loc)
    object_id: str | None = None
    properties: list[tuple[str, Any, Loc]] = field(default_factory=list)
    children: list[Object] = field(default_factory=list)


@dataclass
class Document:
    imports: list[Import] = field(default_factory=list)
    root: Object | None = None
