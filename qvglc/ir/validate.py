from __future__ import annotations

from .constants import NODE_KIND, QVGLIR_VERSION
from .model import Module


class IrValidationError(Exception):
    pass


def validate(module: Module) -> None:
    if module.version != QVGLIR_VERSION:
        raise IrValidationError(f"unsupported IR version {module.version}")

    if not module.module or not module.module[0].isalpha():
        raise IrValidationError(f"invalid module name {module.module!r}")

    if module.root < 0 or module.root >= len(module.nodes):
        raise IrValidationError(f"root index {module.root} out of range")

    ids: dict[str, int] = {}
    for i, node in enumerate(module.nodes):
        if node.kind not in NODE_KIND:
            raise IrValidationError(f"node {i}: unknown kind {node.kind!r}")
        if node.id:
            if node.id in ids:
                raise IrValidationError(f"duplicate id {node.id!r}")
            ids[node.id] = i
        for c in node.children:
            if c < 0 or c >= len(module.nodes):
                raise IrValidationError(f"node {i}: child {c} out of range")
        if node.parent == -1 and i != module.root:
            if not _is_reachable(module, module.root, i):
                raise IrValidationError(f"node {i} not reachable from root")

    for b in module.bindings:
        if b.target not in ids:
            raise IrValidationError(f"binding target id {b.target!r} not found")

    for h in module.handlers:
        if h.node not in ids:
            raise IrValidationError(f"handler node id {h.node!r} not found")


def _is_reachable(module: Module, root: int, target: int) -> bool:
    stack = [root]
    seen = set()
    while stack:
        i = stack.pop()
        if i == target:
            return True
        if i in seen:
            continue
        seen.add(i)
        stack.extend(module.nodes[i].children)
    return False
