from __future__ import annotations

from qvglc.ir.model import Node
from qvglc.layout import NodeLayout

from .arc_gauge import ArcGaugePlan


def _scale_sweep_deg(plan: ArcGaugePlan) -> int:
    start = plan.bg_start % 360
    end = plan.bg_end % 360
    if plan.mode == "LV_ARC_MODE_REVERSE":
        span = (start - end) % 360
    else:
        span = (end - start) % 360
    return span if span else 360


def arc_wants_scale(node: Node) -> bool:
    return int(node.properties.get("tickCount", 0)) > 0


def emit_arc_scale(
    node: Node,
    lay: NodeLayout,
    scale_field: str,
    parent: str,
    plan: ArcGaugePlan,
) -> list[str]:
    ticks = int(node.properties["tickCount"])
    major = int(node.properties.get("majorTickEvery", 5))
    labels = bool(node.properties.get("showTickLabels", False))
    sweep = _scale_sweep_deg(plan)
    r = lay.rect
    var = f"ui->{scale_field}"
    return [
        f"    {var} = lv_scale_create({parent});",
        f"    lv_obj_set_size({var}, {r.w}, {r.h});",
        f"    lv_obj_set_pos({var}, {r.x}, {r.y});",
        f"    lv_scale_set_mode({var}, LV_SCALE_MODE_ROUND_OUTER);",
        f"    lv_scale_set_total_tick_count({var}, {ticks});",
        f"    lv_scale_set_major_tick_every({var}, {major});",
        f"    lv_scale_set_range({var}, {plan.min_i32}, {plan.max_i32});",
        f"    lv_scale_set_angle_range({var}, {sweep});",
        f"    lv_scale_set_rotation({var}, {plan.bg_start});",
        f"    lv_scale_set_label_show({var}, {'true' if labels else 'false'});",
        f"    lv_obj_set_style_bg_opa({var}, LV_OPA_TRANSP, 0);",
        f"    lv_obj_set_style_border_width({var}, 0, 0);",
        f"    lv_obj_set_style_pad_all({var}, 0, 0);",
        f"    lv_obj_set_style_length({var}, 4, LV_PART_ITEMS);",
        f"    lv_obj_set_style_length({var}, 8, LV_PART_INDICATOR);",
        f"    lv_obj_remove_flag({var}, LV_OBJ_FLAG_CLICKABLE);",
    ]
