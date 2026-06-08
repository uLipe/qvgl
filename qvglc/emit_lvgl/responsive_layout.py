from __future__ import annotations

from typing import Any

from qvglc.ir.model import Module, Node


def module_uses_responsive_layout(mod: Module) -> bool:
    return any(n.kind in ("ColumnLayout", "RowLayout") for n in mod.nodes)


def hybrid_module_responsive(mod: Module) -> bool:
    return True


def anchors_fill_parent(node: Node) -> bool:
    anchors = node.properties.get("anchors", {})
    return isinstance(anchors, dict) and anchors.get("fill") == "parent"


def anchors_center_in(node: Node) -> bool:
    anchors = node.properties.get("anchors", {})
    return isinstance(anchors, dict) and "centerIn" in anchors


def anchor_margins(node: Node) -> tuple[int, int, int, int]:
    anchors = node.properties.get("anchors", {})
    if not isinstance(anchors, dict):
        return 0, 0, 0, 0
    if "margins" in anchors:
        m = int(anchors["margins"])
        return m, m, m, m
    return (
        int(anchors.get("leftMargin", 0)),
        int(anchors.get("topMargin", 0)),
        int(anchors.get("rightMargin", 0)),
        int(anchors.get("bottomMargin", 0)),
    )


def _layout_props(node: Node) -> dict[str, Any]:
    lay = node.properties.get("layout", {})
    if not isinstance(lay, dict):
        return {}
    return {k: v for k, v in lay.items() if not (isinstance(v, dict) and "binding" in v)}


def layout_fill_width(node: Node) -> bool:
    return bool(_layout_props(node).get("fillWidth"))


def layout_fill_height(node: Node) -> bool:
    return bool(_layout_props(node).get("fillHeight"))


def emit_pct_fill(field: str) -> list[str]:
    return [
        f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
        f"    lv_obj_set_height(ui->{field}, LV_PCT(100));",
    ]


def emit_flex_column(field: str, spacing: int, margins: tuple[int, int, int, int]) -> list[str]:
    left, top, right, bottom = margins
    lines = [
        f"    lv_obj_set_layout(ui->{field}, LV_LAYOUT_FLEX);",
        f"    lv_obj_set_flex_flow(ui->{field}, LV_FLEX_FLOW_COLUMN);",
        f"    lv_obj_set_flex_align(ui->{field}, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_START);",
        f"    lv_obj_set_style_pad_row(ui->{field}, {spacing}, 0);",
    ]
    if left or top or right or bottom:
        lines.append(
            f"    lv_obj_set_style_pad_left(ui->{field}, {left}, 0);"
        )
        lines.append(f"    lv_obj_set_style_pad_top(ui->{field}, {top}, 0);")
        lines.append(f"    lv_obj_set_style_pad_right(ui->{field}, {right}, 0);")
        lines.append(f"    lv_obj_set_style_pad_bottom(ui->{field}, {bottom}, 0);")
    elif spacing == 0:
        pass
    return lines


def emit_flex_row(field: str, spacing: int) -> list[str]:
    return [
        f"    lv_obj_set_layout(ui->{field}, LV_LAYOUT_FLEX);",
        f"    lv_obj_set_flex_flow(ui->{field}, LV_FLEX_FLOW_ROW);",
        f"    lv_obj_set_flex_align(ui->{field}, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);",
        f"    lv_obj_set_style_pad_column(ui->{field}, {spacing}, 0);",
    ]


def emit_flex_grow_column_child(field: str) -> list[str]:
    return [
        f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
        f"    lv_obj_set_flex_grow(ui->{field}, 1);",
    ]


def emit_flex_grow_row_child(field: str) -> list[str]:
    return [
        f"    lv_obj_set_flex_grow(ui->{field}, 1);",
        f"    lv_label_set_long_mode(ui->{field}, LV_LABEL_LONG_DOT);",
    ]


def emit_widget_geometry(
    field: str,
    parent_node: Node,
    responsive: bool,
    w: int,
    h: int,
    rel_x: int,
    rel_y: int,
) -> list[str]:
    if not responsive:
        return [
            f"    lv_obj_set_size(ui->{field}, {w}, {h});",
            f"    lv_obj_set_pos(ui->{field}, {rel_x}, {rel_y});",
        ]
    if parent_node.kind == "RowLayout":
        return [f"    lv_obj_set_size(ui->{field}, {w}, {h});"]
    if parent_node.kind == "ColumnLayout":
        return [
            f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
            f"    lv_obj_set_height(ui->{field}, {h});",
        ]
    return [
        f"    lv_obj_set_size(ui->{field}, {w}, {h});",
        f"    lv_obj_set_pos(ui->{field}, {rel_x}, {rel_y});",
    ]


def emit_tool_button_geometry(field: str, parent_node: Node, responsive: bool, w: int, h: int, rel_x: int, rel_y: int) -> list[str]:
    if responsive and parent_node.kind in ("RowLayout", "ColumnLayout"):
        return [
            f"    lv_obj_set_width(ui->{field}, LV_SIZE_CONTENT);",
            f"    lv_obj_set_height(ui->{field}, LV_SIZE_CONTENT);",
        ]
    return emit_widget_geometry(field, parent_node, responsive, w, h, rel_x, rel_y)
