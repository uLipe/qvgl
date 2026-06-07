from __future__ import annotations

from typing import Any

from .model import Module


def module_to_dict(module: Module) -> dict[str, Any]:
    nodes = []
    for n in module.nodes:
        raw: dict[str, Any] = {
            "kind": n.kind,
            "children": list(n.children),
            "properties": _dump_properties(n.properties),
        }
        if n.id:
            raw["id"] = n.id
        if n.name:
            raw["name"] = n.name
        if n.flags:
            raw["flags"] = list(n.flags)
        nodes.append(raw)

    module_properties = []
    for mp in module.module_properties:
        entry: dict[str, Any] = {"name": mp.name, "type": mp.type}
        if mp.default is not None:
            entry["default"] = mp.default
        module_properties.append(entry)

    bindings = [
        {"target": b.target, "key": b.key, "expr": b.expr}
        for b in module.bindings
    ]

    handlers = [
        {"node": h.node, "signal": h.signal, "handler": h.handler}
        for h in module.handlers
    ]

    out: dict[str, Any] = {
        "version": module.version,
        "profile": module.profile,
        "module": module.module,
        "root": module.root,
        "nodes": nodes,
    }
    if module_properties:
        out["module_properties"] = module_properties
    if bindings:
        out["bindings"] = bindings
    if handlers:
        out["handlers"] = handlers
    return out


def _dump_properties(props: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in props.items():
        out[k] = v
    return out
