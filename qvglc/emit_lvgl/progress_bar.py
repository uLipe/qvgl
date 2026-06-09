from __future__ import annotations

from dataclasses import dataclass

from qvglc.emit_lvgl.slider import SLIDER_RANGE_I32, _float_c_literal, slider_initial, value_to_i32
from qvglc.ir.model import Module, Node


@dataclass(frozen=True)
class ProgressBarEmitPlan:
    min_value: float
    max_value: float
    range_i32: int = SLIDER_RANGE_I32
    initial_i32: int = 0


def plan_progress_bar(node: Node, initial: float) -> ProgressBarEmitPlan:
    vmin = float(node.properties.get("from", 0))
    vmax = float(node.properties.get("to", 1))
    return ProgressBarEmitPlan(
        min_value=vmin,
        max_value=vmax,
        initial_i32=value_to_i32(initial, vmin, vmax, SLIDER_RANGE_I32),
    )


def progress_initial(node: Node, mod: Module, consumers: dict) -> float:
    return slider_initial(node, mod, consumers)


def emit_progress_value_update(var: str, expr_f32: str, plan: ProgressBarEmitPlan) -> str:
    return (
        f"    qvgl_controls_set_progress_value({var}, ({expr_f32}), "
        f"{_float_c_literal(plan.min_value)}, {_float_c_literal(plan.max_value)});"
    )


def emit_progress_bar_create(
    field: str,
    parent: str,
    plan: ProgressBarEmitPlan,
    geom: list[str],
) -> list[str]:
    return [
        f"    ui->{field} = lv_bar_create({parent});",
        *geom,
        f"    lv_bar_set_range(ui->{field}, 0, {plan.range_i32});",
        f"    lv_bar_set_value(ui->{field}, {plan.initial_i32}, LV_ANIM_OFF);",
    ]
