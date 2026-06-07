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
    clamp = (
        f"{ind}int32_t arc_val = (int32_t)lroundf(({expr_f32}) * {plan.scale}.0f);\n"
        f"{ind}if(arc_val < {plan.min_i32}) arc_val = {plan.min_i32};\n"
        f"{ind}if(arc_val > {plan.max_i32}) arc_val = {plan.max_i32};"
    )
    if plan.value_anim_ms <= 0:
        return f"{clamp}\n{ind}lv_arc_set_value({var}, arc_val);"

    return (
        f"{clamp}\n"
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
        f"{ind}    lv_arc_set_value({var}, arc_val);\n"
        f"{ind}}}"
    )


ARC_ANIM_STATIC_CB = """static void qvgl_arc_anim_exec_cb(void * var, int32_t v)
{
    lv_arc_set_value((lv_obj_t *)var, v);
}
"""
