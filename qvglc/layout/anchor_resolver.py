from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qvglc.ir.model import Module, Node


class LayoutError(Exception):
    pass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def center_x(self) -> int:
        return self.x + self.w // 2

    @property
    def center_y(self) -> int:
        return self.y + self.h // 2


@dataclass(frozen=True)
class NodeLayout:
    rect: Rect
    align_center: bool = False
    align_center_offset_y: int = 0


def resolve_layout(mod: Module) -> dict[int, NodeLayout]:
    by_id = {n.id: i for i, n in enumerate(mod.nodes) if n.id}
    resolved: dict[int, NodeLayout] = {}

    def parent_rect(node_idx: int) -> Rect:
        parent_idx = mod.nodes[node_idx].parent
        if parent_idx < 0:
            return Rect(0, 0, 0, 0)
        return resolved[parent_idx].rect

    def walk(idx: int) -> None:
        node = mod.nodes[idx]
        if idx == mod.root:
            w = int(node.properties.get("width", 400))
            h = int(node.properties.get("height", 400))
            resolved[idx] = NodeLayout(Rect(0, 0, w, h))
        else:
            resolved[idx] = _resolve_node(mod, idx, parent_rect(idx), resolved, by_id)
        for child in node.children:
            walk(child)

    walk(mod.root)

    from .flex_layout import apply_flex_layout

    return apply_flex_layout(mod, resolved)


def _resolve_node(
    mod: Module,
    idx: int,
    parent: Rect,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
) -> NodeLayout:
    node = mod.nodes[idx]
    anchors = node.properties.get("anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}

    margins = _anchor_margins(anchors)
    w, h = _intrinsic_size(node)

    if anchors.get("fill") == "parent":
        return NodeLayout(_inset_rect(parent, margins))

    if "centerIn" in anchors and not _has_edge_anchor(anchors):
        box = _anchor_target_rect(anchors["centerIn"], mod, resolved, by_id, parent)
        if node.kind == "Text":
            return NodeLayout(box, align_center=True)
        if w > 0 and h > 0:
            return NodeLayout(_center_rect(box, w, h))
        return NodeLayout(box, align_center=True)

    rect = _resolve_box(mod, idx, parent, resolved, by_id, anchors, margins, w, h)

    if "centerIn" in anchors:
        box = _anchor_target_rect(anchors["centerIn"], mod, resolved, by_id, parent)
        offset_y = rect.center_y - box.center_y
        return NodeLayout(box, align_center=True, align_center_offset_y=offset_y)

    if node.kind == "Text" and not _is_stretched(anchors):
        offset_y = rect.center_y - parent.center_y
        return NodeLayout(parent, align_center=True, align_center_offset_y=offset_y)

    return NodeLayout(rect)


def _resolve_box(
    mod: Module,
    idx: int,
    parent: Rect,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    anchors: dict[str, Any],
    margins: dict[str, int],
    w: int,
    h: int,
) -> Rect:
    x = parent.x
    y = parent.y
    rw = max(w, 1)
    rh = max(h, 1)

    if "left" in anchors and "right" in anchors:
        left = _anchor_line_x(anchors["left"], mod, resolved, by_id, parent) + margins.get("left", 0)
        right = _anchor_line_x(anchors["right"], mod, resolved, by_id, parent) - margins.get("right", 0)
        x = left
        rw = max(1, right - left)
    elif "left" in anchors:
        x = _anchor_line_x(anchors["left"], mod, resolved, by_id, parent) + margins.get("left", 0)
    elif "right" in anchors:
        x = _anchor_line_x(anchors["right"], mod, resolved, by_id, parent) - rw - margins.get("right", 0)
    elif "horizontalCenter" in anchors:
        cx = _anchor_line_x(anchors["horizontalCenter"], mod, resolved, by_id, parent)
        x = cx - rw // 2
    elif _is_hcenter(anchors):
        x = parent.center_x - rw // 2

    if "top" in anchors and "bottom" in anchors:
        top = _anchor_line_y(anchors["top"], mod, resolved, by_id, parent) + margins.get("top", 0)
        bottom = _anchor_line_y(anchors["bottom"], mod, resolved, by_id, parent) - margins.get("bottom", 0)
        y = top
        rh = max(1, bottom - top)
    elif "top" in anchors:
        y = _anchor_line_y(anchors["top"], mod, resolved, by_id, parent) + margins.get("top", 0)
    elif "bottom" in anchors:
        margin = int(anchors.get("bottomMargin", margins.get("bottom", 0)))
        y_line = _anchor_line_y(anchors["bottom"], mod, resolved, by_id, parent)
        ref = anchors["bottom"]
        if isinstance(ref, str) and (ref.endswith(".bottom") or ref == "parent.bottom"):
            y = y_line - margin - rh
        else:
            y = y_line + margin - rh
    elif _is_vcenter(anchors):
        y = parent.center_y - rh // 2

    return Rect(x, y, rw, rh)


def _center_rect(parent: Rect, w: int, h: int) -> Rect:
    return Rect(
        parent.x + (parent.w - w) // 2,
        parent.y + (parent.h - h) // 2,
        w,
        h,
    )


def _anchor_target_rect(
    ref: str,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    parent: Rect,
) -> Rect:
    if ref == "parent":
        return parent
    if ref not in by_id:
        raise LayoutError(f"unknown centerIn target {ref!r}")
    idx = by_id[ref]
    lay = resolved.get(idx)
    if lay is None:
        raise LayoutError(f"centerIn target {ref!r} not laid out yet")
    return lay.rect


def _has_edge_anchor(anchors: dict[str, Any]) -> bool:
    return any(k in anchors for k in ("left", "right", "top", "bottom", "horizontalCenter", "verticalCenter"))


def _is_stretched(anchors: dict[str, Any]) -> bool:
    return ("left" in anchors and "right" in anchors) or ("top" in anchors and "bottom" in anchors)


def _is_hcenter(anchors: dict[str, Any]) -> bool:
    hc = anchors.get("horizontalCenter")
    return hc in ("parent", "parent.horizontalCenter")


def _is_vcenter(anchors: dict[str, Any]) -> bool:
    vc = anchors.get("verticalCenter")
    return vc in ("parent", "parent.verticalCenter")


def _anchor_margins(anchors: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for key in ("top", "bottom", "left", "right"):
        margin_key = f"{key}Margin"
        if margin_key in anchors:
            out[key] = int(anchors[margin_key])
    if "margins" in anchors:
        m = int(anchors["margins"])
        out = {"top": m, "bottom": m, "left": m, "right": m}
    return out


def _inset_rect(parent: Rect, margins: dict[str, int]) -> Rect:
    left = margins.get("left", 0)
    top = margins.get("top", 0)
    right = margins.get("right", 0)
    bottom = margins.get("bottom", 0)
    return Rect(
        parent.x + left,
        parent.y + top,
        max(1, parent.w - left - right),
        max(1, parent.h - top - bottom),
    )


def _intrinsic_size(node: Node) -> tuple[int, int]:
    w = int(node.properties["width"]) if "width" in node.properties else 0
    h = int(node.properties["height"]) if "height" in node.properties else 0
    if node.kind in ("Text", "ToolButton") and (w <= 0 or h <= 0):
        text = node.properties.get("text", "")
        if isinstance(text, dict):
            text = "-0.7 bar"
        px = int(node.properties.get("font.pixelSize", 14))
        tw = max(1, int(len(str(text)) * px * 0.55))
        th = max(1, px)
        if node.kind == "ToolButton":
            tw = max(tw + 16, 28)
            th = max(th + 8, 28)
        return (tw if w <= 0 else w, th if h <= 0 else h)
    return (w, h)


def _anchor_line_x(
    ref: Any,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    parent: Rect,
) -> int:
    if ref in ("parent", "parent.left"):
        return parent.x
    if ref == "parent.right":
        return parent.right
    if ref == "parent.horizontalCenter":
        return parent.center_x
    if isinstance(ref, str) and ref.endswith(".left"):
        return _node_edge_x(ref[: -len(".left")], mod, resolved, by_id, "left")
    if isinstance(ref, str) and ref.endswith(".right"):
        return _node_edge_x(ref[: -len(".right")], mod, resolved, by_id, "right")
    if isinstance(ref, str) and ref.endswith(".horizontalCenter"):
        return _node_edge_x(ref[: -len(".horizontalCenter")], mod, resolved, by_id, "center_x")
    raise LayoutError(f"unsupported anchor x ref {ref!r}")


def _anchor_line_y(
    ref: Any,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    parent: Rect,
) -> int:
    if ref in ("parent", "parent.top"):
        return parent.y
    if ref == "parent.bottom":
        return parent.bottom
    if ref == "parent.verticalCenter":
        return parent.center_y
    if isinstance(ref, str) and ref.endswith(".top"):
        return _node_edge_y(ref[: -len(".top")], mod, resolved, by_id, "top")
    if isinstance(ref, str) and ref.endswith(".bottom"):
        return _node_edge_y(ref[: -len(".bottom")], mod, resolved, by_id, "bottom")
    if isinstance(ref, str) and ref.endswith(".verticalCenter"):
        return _node_edge_y(ref[: -len(".verticalCenter")], mod, resolved, by_id, "center_y")
    raise LayoutError(f"unsupported anchor y ref {ref!r}")


def _node_effective_rect(
    ref_id: str,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
) -> Rect:
    if ref_id not in by_id:
        raise LayoutError(f"unknown anchor ref id {ref_id!r}")
    ref_idx = by_id[ref_id]
    ref_lay = resolved.get(ref_idx)
    if ref_lay is None:
        raise LayoutError(f"anchor ref {ref_id!r} used before layout")
    ref_node = mod.nodes[ref_idx]
    w, h = _intrinsic_size(ref_node)
    if ref_lay.align_center:
        parent = resolved[ref_node.parent].rect
        cx = parent.center_x
        cy = parent.center_y + ref_lay.align_center_offset_y
        return Rect(cx - w // 2, cy - h // 2, w, h)
    return ref_lay.rect


def _node_edge_x(
    ref_id: str,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    edge: str,
) -> int:
    r = _node_effective_rect(ref_id, mod, resolved, by_id)
    if edge == "left":
        return r.x
    if edge == "right":
        return r.right
    return r.center_x


def _node_edge_y(
    ref_id: str,
    mod: Module,
    resolved: dict[int, NodeLayout],
    by_id: dict[str, int],
    edge: str,
) -> int:
    r = _node_effective_rect(ref_id, mod, resolved, by_id)
    if edge == "top":
        return r.y
    if edge == "bottom":
        return r.bottom
    return r.center_y
