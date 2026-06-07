from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import Binding, Handler, Module, ModuleProperty, Node


def load_json_path(path: Path | str) -> Module:
    with open(path, encoding="utf-8") as f:
        return load_json_data(json.load(f))


def load_json_data(data: dict[str, Any]) -> Module:
    nodes: list[Node] = []
    for raw in data["nodes"]:
        nodes.append(
            Node(
                kind=raw["kind"],
                children=list(raw.get("children", [])),
                id=raw.get("id"),
                name=raw.get("name"),
                properties=dict(raw.get("properties", {})),
                flags=list(raw.get("flags", [])),
            )
        )

    for i, node in enumerate(nodes):
        for child in node.children:
            if child < 0 or child >= len(nodes):
                raise ValueError(f"node {i}: child index {child} out of range")
            if nodes[child].parent != -1:
                raise ValueError(f"node {child}: multiple parents")
            nodes[child].parent = i

    module_props = [
        ModuleProperty(
            name=p["name"],
            type=p["type"],
            default=p.get("default"),
        )
        for p in data.get("module_properties", [])
    ]

    bindings = [
        Binding(target=b["target"], key=b["key"], expr=b["expr"])
        for b in data.get("bindings", [])
    ]

    handlers = [
        Handler(node=h["node"], signal=h["signal"], handler=h["handler"])
        for h in data.get("handlers", [])
    ]

    return Module(
        version=int(data["version"]),
        profile=str(data["profile"]),
        module=str(data["module"]),
        root=int(data["root"]),
        nodes=nodes,
        module_properties=module_props,
        bindings=bindings,
        handlers=handlers,
    )
