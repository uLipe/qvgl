from __future__ import annotations

from dataclasses import dataclass

from qvglc.ir.model import Module, Node


SLIDER_RANGE_I32 = 1000


@dataclass(frozen=True)
class SliderEmitPlan:
    min_value: float
    max_value: float
    range_i32: int = SLIDER_RANGE_I32
    initial_i32: int = 0


def _float_c_literal(value: float) -> str:
    s = f"{value:.6g}"
    if "." not in s and "e" not in s and "E" not in s:
        s += ".0"
    return f"{s}f"


def value_to_i32(value: float, vmin: float, vmax: float, range_i32: int) -> int:
    if abs(vmax - vmin) < 1e-9:
        return 0
    t = (value - vmin) / (vmax - vmin)
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    return int(round(t * range_i32))


def plan_slider(node: Node, initial: float) -> SliderEmitPlan:
    vmin = float(node.properties.get("from", 0))
    vmax = float(node.properties.get("to", 1))
    return SliderEmitPlan(
        min_value=vmin,
        max_value=vmax,
        initial_i32=value_to_i32(initial, vmin, vmax, SLIDER_RANGE_I32),
    )


def slider_initial(node: Node, mod: Module, consumers: dict) -> float:
    value = node.properties.get("value")
    if isinstance(value, dict) and "binding" in value:
        sym = value["binding"].get("sym")
        if sym:
            for prop in mod.module_properties:
                if prop.name == sym and prop.default is not None:
                    return float(prop.default)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def emit_slider_value_update(var: str, expr_f32: str, plan: SliderEmitPlan) -> str:
    return (
        f"    qvgl_widget_set_slider_value({var}, ({expr_f32}), "
        f"{_float_c_literal(plan.min_value)}, {_float_c_literal(plan.max_value)});"
    )


def emit_slider_create(
    field: str,
    parent: str,
    plan: SliderEmitPlan,
    geom: list[str],
    *,
    handler_cbs: list[str] | None = None,
) -> list[str]:
    lines = [
        f"    ui->{field} = lv_slider_create({parent});",
        *geom,
        f"    lv_slider_set_range(ui->{field}, 0, {plan.range_i32});",
        f"    lv_slider_set_value(ui->{field}, {plan.initial_i32}, LV_ANIM_OFF);",
    ]
    for cb in handler_cbs or []:
        lines.append(
            f"    lv_obj_add_event_cb(ui->{field}, {cb}, LV_EVENT_VALUE_CHANGED, NULL);"
        )
    return lines
