from __future__ import annotations

from typing import Any

from qvglc.emit_lvgl.arc_anim import emit_arc_value_update
from qvglc.emit_lvgl.arc_gauge import ArcGaugePlan
from qvglc.ir.model import Module, ModuleProperty

from .errors import EmitError

STRING_FIELD_LEN = 64

_C_PARAM: dict[str, tuple[str, str]] = {
    "f32": ("float", "f"),
    "f64": ("float", "f"),
    "i32": ("int32_t", ""),
    "bool": ("bool", ""),
    "str": ("const char *", ""),
}


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


def struct_field_decl(prop: ModuleProperty) -> str:
    if prop.type in ("f32", "f64"):
        return f"    float {prop.name};"
    if prop.type == "i32":
        return f"    int32_t {prop.name};"
    if prop.type == "bool":
        return f"    bool {prop.name};"
    if prop.type == "str":
        return f"    char {prop.name}[{STRING_FIELD_LEN}];"
    raise EmitError(f"unsupported module property type {prop.type!r}")


def _float_c_literal(value: float) -> str:
    s = f"{value:.6g}"
    if "." not in s and "e" not in s and "E" not in s:
        s += ".0"
    return f"{s}f"


def struct_field_init(prop: ModuleProperty) -> str:
    if prop.type in ("f32", "f64"):
        default = 0.0 if prop.default is None else float(prop.default)
        return f"    ui->{prop.name} = {_float_c_literal(default)};"
    if prop.type == "i32":
        default = 0 if prop.default is None else int(prop.default)
        return f"    ui->{prop.name} = {default};"
    if prop.type == "bool":
        default = False if prop.default is None else bool(prop.default)
        return f"    ui->{prop.name} = {'true' if default else 'false'};"
    if prop.type == "str":
        default = "" if prop.default is None else str(prop.default)
        escaped = default.replace("\\", "\\\\").replace('"', '\\"')
        return f'    lv_snprintf(ui->{prop.name}, sizeof(ui->{prop.name}), "%s", "{escaped}");'
    raise EmitError(f"unsupported module property type {prop.type!r}")


def setter_decl(mod: Module, prop: ModuleProperty) -> str:
    ctype, _ = _C_PARAM[prop.type]
    return f"void qvgl_{mod.module}_set_{prop.name}(qvgl_ui_{mod.module}_t * ui, {ctype} {prop.name});"


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
        f"    qvgl_widget_set_text(ui->{field}, buf);"
    )


def _emit_text_consumer(
    prop: ModuleProperty, field: str, param: str, expr: dict[str, Any]
) -> str:
    if prop.type == "str":
        if "sym" not in expr:
            raise EmitError("string property text binding requires sym")
        return f"    qvgl_widget_set_text(ui->{field}, {param});"
    if prop.type == "i32":
        if "sym" in expr:
            return (
                f"    char buf[32];\n"
                f'    lv_snprintf(buf, sizeof(buf), "%d", (int){param});\n'
                f"    qvgl_widget_set_text(ui->{field}, buf);"
            )
        return _emit_label_format(expr, field, param)
    if prop.type in ("f32", "f64"):
        if "sym" in expr:
            return (
                f"    char buf[32];\n"
                f'    lv_snprintf(buf, sizeof(buf), "%.2f", (double){param});\n'
                f"    qvgl_widget_set_text(ui->{field}, buf);"
            )
        return _emit_label_format(expr, field, param)
    raise EmitError(f"property type {prop.type!r} cannot bind to text")


def _emit_consumer(
    prop: ModuleProperty,
    idx: int,
    key: str,
    expr: dict[str, Any],
    field: str,
    param: str,
    arc_plans: dict[int, ArcGaugePlan],
) -> str:
    if key == "value":
        if prop.type not in ("f32", "f64"):
            raise EmitError(f"binding key value requires real property, got {prop.type!r}")
        plan = arc_plans.get(idx)
        if plan is None:
            raise EmitError(f"binding on non-arc node index {idx}")
        return emit_arc_value_update(f"ui->{field}", param, plan)
    if key == "text":
        return _emit_text_consumer(prop, field, param, expr)
    if key == "visible":
        if prop.type != "bool":
            raise EmitError(f"binding key visible requires bool property, got {prop.type!r}")
        return f"    qvgl_widget_set_visible(ui->{field}, {param});"
    if key == "opacity":
        if prop.type not in ("f32", "f64"):
            raise EmitError(f"binding key opacity requires real property, got {prop.type!r}")
        return f"    qvgl_widget_set_opa_f32(ui->{field}, {param});"
    raise EmitError(f"unsupported binding key {key!r} on {field}")


def emit_setter_body(
    mod: Module,
    prop: ModuleProperty,
    consumers: list[tuple[int, str, dict[str, Any]]],
    field_names: dict[int, str],
    arc_plans: dict[int, ArcGaugePlan],
) -> str:
    ctype, _ = _C_PARAM[prop.type]
    param = prop.name
    lines: list[str] = []
    if prop.type == "str":
        lines.append(f'    lv_snprintf(ui->{param}, sizeof(ui->{param}), "%s", {param} ? {param} : "");')
    else:
        lines.append(f"    ui->{param} = {param};")
    for idx, key, expr in consumers:
        field = field_names[idx]
        lines.append(_emit_consumer(prop, idx, key, expr, field, param, arc_plans))
    body = "\n".join(lines)
    return f"""void qvgl_{mod.module}_set_{prop.name}(qvgl_ui_{mod.module}_t * ui, {ctype} {param})
{{
    if(!ui) return;
{body}
}}
"""
