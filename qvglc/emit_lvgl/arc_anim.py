from __future__ import annotations

from .arc_gauge import ArcGaugePlan


def emit_arc_value_update(
    var: str,
    expr_f32: str,
    plan: ArcGaugePlan,
    *,
    indent: str = "    ",
) -> str:
    ind = indent
    vmin = f"{plan.min_value}f"
    vmax = f"{plan.max_value}f"
    if plan.value_anim_ms <= 0:
        return f"{ind}qvgl_widget_set_arc_value({var}, ({expr_f32}), {vmin}, {vmax});"

    return (
        f"{ind}int32_t arc_val = qvgl_widget_arc_value_for({var}, ({expr_f32}), {vmin}, {vmax});\n"
        f"{ind}if({plan.value_anim_ms} > 0) {{\n"
        f"{ind}    lv_anim_del({var}, NULL);\n"
        f"{ind}    lv_anim_t a;\n"
        f"{ind}    lv_anim_init(&a);\n"
        f"{ind}    lv_anim_set_var(&a, {var});\n"
        f"{ind}    lv_anim_set_exec_cb(&a, qvgl_arc_anim_exec_cb);\n"
        f"{ind}    lv_anim_set_duration(&a, {plan.value_anim_ms});\n"
        f"{ind}    lv_anim_set_values(&a, lv_arc_get_value({var}), arc_val);\n"
        f"{ind}    lv_anim_start(&a);\n"
        f"{ind}}} else {{\n"
        f"{ind}    qvgl_widget_set_arc_i32({var}, arc_val);\n"
        f"{ind}}}"
    )


ARC_ANIM_STATIC_CB = """static void qvgl_arc_anim_exec_cb(void * var, int32_t v)
{
    qvgl_widget_set_arc_i32((lv_obj_t *)var, v);
}
"""
