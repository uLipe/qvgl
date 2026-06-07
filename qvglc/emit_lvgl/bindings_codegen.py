from __future__ import annotations

from typing import Any

from qvglc.emit_lvgl.arc_gauge import ArcGaugePlan, emit_arc_value_update
from qvglc.ir.model import Module

from .errors import EmitError


def expr_symbols(expr: dict[str, Any]) -> set[str]:
    if "sym" in expr:
        return {expr["sym"]}
    if expr.get("op") == "format":
        sym = expr.get("args", [None, {}])[1]
        if isinstance(sym, dict) and "sym" in sym:
            return {sym["sym"]}
    return set()


def property_consumers(mod: Module) -> dict[str, list[tuple[int, str, dict[str, Any]]]]:
    by_id = {n.id: i for i, n in enumerate(mod.nodes) if n.id}
    names = {p.name for p in mod.module_properties}
    out: dict[str, list[tuple[int, str, dict[str, Any]]]] = {n: [] for n in names}
    for binding in mod.bindings:
        for sym in expr_symbols(binding.expr):
            if sym not in out:
                continue
            idx = by_id.get(binding.target)
            if idx is None:
                continue
            out[sym].append((idx, binding.key, binding.expr))
    return out


def _emit_label_format(expr: dict[str, Any], field: str, value_expr: str) -> str:
    if expr.get("op") != "format":
        raise EmitError(f"unsupported text binding: {expr!r}")
    args = expr.get("args", [])
    if len(args) != 2:
        raise EmitError("format expects 2 args")
    fmt = args[0].get("const")
    if not isinstance(fmt, str):
        raise EmitError("format arg0 must be const string")
    return (
        f"    char buf[32];\n"
        f'    lv_snprintf(buf, sizeof(buf), "{fmt}", (double){value_expr});\n'
        f"    lv_label_set_text(ui->{field}, buf);"
    )


def emit_setter_body(
    mod: Module,
    prop_name: str,
    consumers: list[tuple[int, str, dict[str, Any]]],
    field_names: dict[int, str],
    arc_plans: dict[int, ArcGaugePlan],
) -> str:
    param = prop_name
    lines = [f"    ui->{prop_name} = {param};"]
    for idx, key, expr in consumers:
        field = field_names[idx]
        if key == "value":
            plan = arc_plans.get(idx)
            if plan is None:
                raise EmitError(f"binding on non-arc node index {idx}")
            lines.append(emit_arc_value_update(f"ui->{field}", param, plan))
        elif key == "text":
            lines.append(_emit_label_format(expr, field, param))
        else:
            raise EmitError(f"unsupported binding key {key!r} on {field}")
    body = "\n".join(lines)
    return f"""void qvgl_{mod.module}_set_{prop_name}(qvgl_ui_{mod.module}_t * ui, float {param})
{{
    if(!ui) return;
{body}
}}
"""
