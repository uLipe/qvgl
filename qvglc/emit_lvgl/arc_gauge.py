from __future__ import annotations

from dataclasses import dataclass

from .colors import lv_color_hex_expr


@dataclass(frozen=True)
class ArcGaugePlan:
    bg_start: int
    bg_end: int
    mode: str
    min_i32: int
    max_i32: int
    scale: int
    line_width: int
    indicator_color: str
    track_color: str
    initial_i32: int


def _norm_angle(deg: float) -> int:
    a = int(round(deg)) % 360
    if a < 0:
        a += 360
    return a


def _arc_sweep_deg(from_deg: float, to_deg: float) -> float:
    start = from_deg % 360.0
    end = to_deg % 360.0
    if end <= start:
        end += 360.0
    return end - start


def plan_arc_gauge(
    *,
    from_deg: float,
    to_deg: float,
    min_value: float,
    max_value: float,
    line_width: int,
    color: str,
    initial_value: float,
    scale: int = 10,
    track_color: str = "#ff2a2a3e",
) -> ArcGaugePlan:
    start = _norm_angle(from_deg)
    end = _norm_angle(to_deg)

    # Qt Ultralite Arc: when `to` is negative or below `from`, sweep is the long CCW arc.
    reverse = to_deg < 0 or (to_deg < from_deg and _arc_sweep_deg(from_deg, to_deg) > 180.0)
    mode = "LV_ARC_MODE_REVERSE" if reverse else "LV_ARC_MODE_NORMAL"

    min_i32 = int(round(min_value * scale))
    max_i32 = int(round(max_value * scale))
    if min_i32 > max_i32:
        min_i32, max_i32 = max_i32, min_i32

    init = int(round(initial_value * scale))
    if init < min_i32:
        init = min_i32
    if init > max_i32:
        init = max_i32

    return ArcGaugePlan(
        bg_start=start,
        bg_end=end,
        mode=mode,
        min_i32=min_i32,
        max_i32=max_i32,
        scale=scale,
        line_width=line_width,
        indicator_color=color,
        track_color=track_color,
        initial_i32=init,
    )


def emit_arc_gauge_init(var: str, plan: ArcGaugePlan, indent: str = "    ") -> list[str]:
    ind = indent
    ind2 = indent * 2
    track = lv_color_hex_expr(plan.track_color)
    accent = lv_color_hex_expr(plan.indicator_color)
    lw = plan.line_width

    lines = [
        f"{ind}lv_arc_set_bg_angles({var}, {plan.bg_start}, {plan.bg_end});",
        f"{ind}lv_arc_set_mode({var}, {plan.mode});",
        f"{ind}lv_arc_set_range({var}, {plan.min_i32}, {plan.max_i32});",
        f"{ind}lv_arc_set_value({var}, {plan.initial_i32});",
        f"{ind}lv_obj_set_style_arc_width({var}, {lw}, LV_PART_MAIN);",
        f"{ind}lv_obj_set_style_arc_width({var}, {lw}, LV_PART_INDICATOR);",
        f"{ind}lv_obj_set_style_arc_color({var}, {track}, LV_PART_MAIN);",
        f"{ind}lv_obj_set_style_arc_opa({var}, LV_OPA_COVER, LV_PART_MAIN);",
        f"{ind}lv_obj_set_style_arc_rounded({var}, true, LV_PART_MAIN);",
        f"{ind}lv_obj_set_style_arc_rounded({var}, true, LV_PART_INDICATOR);",
        f"{ind}lv_obj_set_style_arc_color({var}, {accent}, LV_PART_INDICATOR);",
        f"{ind}lv_obj_set_style_opa({var}, LV_OPA_TRANSP, LV_PART_KNOB);",
        f"{ind}lv_obj_remove_flag({var}, LV_OBJ_FLAG_CLICKABLE);",
    ]
    return lines


def emit_arc_value_update(var: str, expr_f32: str, plan: ArcGaugePlan, indent: str = "    ") -> str:
    return (
        f"{indent}int32_t arc_val = (int32_t)lroundf(({expr_f32}) * {plan.scale}.0f);\n"
        f"{indent}if(arc_val < {plan.min_i32}) arc_val = {plan.min_i32};\n"
        f"{indent}if(arc_val > {plan.max_i32}) arc_val = {plan.max_i32};\n"
        f"{indent}lv_arc_set_value({var}, arc_val);"
    )


def f32_scale_for_range(min_v: float, max_v: float) -> int:
    max_decimals = 0
    for v in (min_v, max_v):
        frac = f"{v:.6f}".split(".")[1].rstrip("0")
        if frac:
            max_decimals = max(max_decimals, len(frac))
    if max_decimals == 0:
        return 1
    return int(10 ** min(max_decimals, 3))
