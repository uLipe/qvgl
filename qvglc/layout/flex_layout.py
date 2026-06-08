from __future__ import annotations

from typing import Any

from qvglc.ir.model import Module, Node

from .anchor_resolver import Rect, _has_edge_anchor, _intrinsic_size
from .anchor_resolver import NodeLayout


def apply_flex_layout(mod: Module, layouts: dict[int, NodeLayout]) -> dict[int, NodeLayout]:
    out = dict(layouts)

    def visit(parent_idx: int) -> None:
        parent = mod.nodes[parent_idx]
        if parent.kind in ("ColumnLayout", "RowLayout"):
            _layout_children(mod, parent_idx, parent, out)
        for child_idx in parent.children:
            visit(child_idx)

    visit(mod.root)
    return out


def _layout_children(
    mod: Module,
    parent_idx: int,
    parent: Node,
    layouts: dict[int, NodeLayout],
) -> None:
    parent_rect = layouts[parent_idx].rect
    spacing = int(parent.properties.get("spacing", 0))
    is_column = parent.kind == "ColumnLayout"

    flex_children: list[int] = []
    for child_idx in parent.children:
        child = mod.nodes[child_idx]
        anchors = child.properties.get("anchors", {})
        if not isinstance(anchors, dict):
            anchors = {}
        if anchors.get("fill") == "parent" or _has_edge_anchor(anchors):
            continue
        flex_children.append(child_idx)

    if not flex_children:
        return

    fixed: list[int] = []
    fill: list[int] = []
    for child_idx in flex_children:
        lay = _layout_props(mod.nodes[child_idx])
        if lay.get("fillHeight" if is_column else "fillWidth"):
            fill.append(child_idx)
        else:
            fixed.append(child_idx)

    main_avail = parent_rect.h if is_column else parent_rect.w
    main_avail -= spacing * max(0, len(flex_children) - 1)

    fixed_sizes: dict[int, int] = {}
    for child_idx in fixed:
        child = mod.nodes[child_idx]
        lay = _layout_props(child)
        pref_key = "preferredHeight" if is_column else "preferredWidth"
        if pref_key in lay:
            fixed_sizes[child_idx] = max(1, int(lay[pref_key]))
            continue
        if child.kind == "RowLayout" and is_column:
            fixed_sizes[child_idx] = max(1, _row_main_size(mod, child_idx))
            continue
        if child.kind == "ColumnLayout" and not is_column:
            fixed_sizes[child_idx] = max(1, _column_main_size(mod, child_idx))
            continue
        w, h = _intrinsic_size(child)
        fixed_sizes[child_idx] = max(1, h if is_column else w)

    remaining = main_avail - sum(fixed_sizes.values())
    fill_size = max(1, remaining // len(fill)) if fill else 0

    main_pos = parent_rect.y if is_column else parent_rect.x
    cross_pos = parent_rect.x if is_column else parent_rect.y
    cross_size = parent_rect.w if is_column else parent_rect.h

    for child_idx in fixed + fill:
        child = mod.nodes[child_idx]
        lay = _layout_props(child)
        main_size = fill_size if child_idx in fill else fixed_sizes[child_idx]
        cross_fill = bool(lay.get("fillWidth" if is_column else "fillHeight", False))

        if is_column:
            w = cross_size if cross_fill else _cross_size(child, lay, cross_size, horizontal=True)
            h = main_size
            x = cross_pos if cross_fill else cross_pos + (cross_size - w) // 2
            y = main_pos
        else:
            w = main_size
            h = cross_size if cross_fill else _cross_size(child, lay, cross_size, horizontal=False)
            x = main_pos
            y = cross_pos if cross_fill else cross_pos + (cross_size - h) // 2

        layouts[child_idx] = NodeLayout(
            Rect(x, y, max(1, w), max(1, h)),
            False,
            0,
        )
        main_pos += main_size + spacing


def _layout_props(node: Node) -> dict[str, Any]:
    lay = node.properties.get("layout", {})
    if not isinstance(lay, dict):
        return {}
    out: dict[str, Any] = {}
    for key, val in lay.items():
        if isinstance(val, dict) and "binding" in val:
            continue
        out[key] = val
    return out


def _row_main_size(mod: Module, idx: int) -> int:
    node = mod.nodes[idx]
    spacing = int(node.properties.get("spacing", 0))
    total = 0
    count = 0
    for child_idx in node.children:
        child = mod.nodes[child_idx]
        if _layout_props(child).get("fillHeight"):
            continue
        _, h = _intrinsic_size(child)
        total = max(total, h)
        count += 1
    return max(total, 28)


def _column_main_size(mod: Module, idx: int) -> int:
    node = mod.nodes[idx]
    spacing = int(node.properties.get("spacing", 0))
    total = 0
    count = 0
    for child_idx in node.children:
        child = mod.nodes[child_idx]
        if _layout_props(child).get("fillWidth"):
            continue
        w, _ = _intrinsic_size(child)
        total += w
        count += 1
    if count > 1:
        total += spacing * (count - 1)
    return max(total, 1)


def _cross_size(node: Node, lay: dict[str, Any], cross_size: int, *, horizontal: bool) -> int:
    pref_key = "preferredWidth" if horizontal else "preferredHeight"
    if pref_key in lay:
        return max(1, int(lay[pref_key]))
    w, h = _intrinsic_size(node)
    return max(1, w if horizontal else h)
