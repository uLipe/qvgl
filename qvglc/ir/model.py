from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModuleProperty:
    name: str
    type: str
    default: Any = None


@dataclass
class Node:
    kind: str
    children: list[int] = field(default_factory=list)
    id: str | None = None
    name: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    parent: int = -1


@dataclass
class Binding:
    target: str
    key: str
    expr: dict[str, Any]


@dataclass
class Handler:
    node: str
    signal: str
    handler: str


@dataclass
class Module:
    version: int
    profile: str
    module: str
    root: int
    nodes: list[Node]
    module_properties: list[ModuleProperty] = field(default_factory=list)
    bindings: list[Binding] = field(default_factory=list)
    handlers: list[Handler] = field(default_factory=list)
