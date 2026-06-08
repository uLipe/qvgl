from __future__ import annotations

from dataclasses import dataclass

from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.emit_lvgl.widget_style import lv_font_expr
from qvglc.emit_lvgl.bindings_codegen import property_consumers
from qvglc.ir.model import Module, Node
from qvglc.layout import NodeLayout


@dataclass(frozen=True)
class LinePlotEmitPlan:
    field: str
    grid_div: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    chart_x: int
    chart_y: int
    chart_w: int
    chart_h: int
    point_count: int
    hover_enabled: bool


@dataclass(frozen=True)
class LinePlotHoverPlan:
    plot_field: str
    cursor_field: str


def _float_c_literal(value: float) -> str:
    s = f"{value:.6g}"
    if "." not in s and "e" not in s and "E" not in s:
        s += ".0"
    return f"{s}f"


def plan_line_plot(node: Node, lay: NodeLayout) -> LinePlotEmitPlan:
    r = lay.rect
    pad_l = int(node.properties.get("padL", 52))
    pad_r = int(node.properties.get("padR", 10))
    pad_t = int(node.properties.get("padT", 10))
    pad_b = int(node.properties.get("padB", 30))
    chart_w = max(1, r.w - pad_l - pad_r)
    chart_h = max(1, r.h - pad_t - pad_b)
    series = node.properties.get("series", [])
    return LinePlotEmitPlan(
        field="",
        grid_div=int(node.properties.get("gridDiv", 4)),
        x_min=float(node.properties.get("xMin", 0)),
        x_max=float(node.properties.get("xMax", 5)),
        y_min=float(node.properties.get("yMin", -1.1)),
        y_max=float(node.properties.get("yMax", 1.3)),
        chart_x=pad_l,
        chart_y=pad_t,
        chart_w=chart_w,
        chart_h=chart_h,
        point_count=len(series),
        hover_enabled=bool(node.properties.get("hoverEnabled")),
    )


def emit_line_plot_struct_field(field: str) -> str:
    return f"    qvgl_plot_t {field}_plot;"


def emit_line_plot_initial_series(node: Node, field: str) -> list[str]:
    series = node.properties.get("series", [])
    if not series:
        return []
    items = ", ".join(
        f"{{ {_float_c_literal(float(p['x']))}, {_float_c_literal(float(p['y']))} }}"
        for p in series
    )
    n = len(series)
    return [
        f"static const qvgl_plot_point_t qvgl_{field}_initial[{n}] = {{ {items} }};",
    ]


def cursor_text_property(mod: Module) -> str | None:
    consumers = property_consumers(mod)
    cursor_idx = next(
        (i for i, n in enumerate(mod.nodes) if n.id == "cursorLabel" and n.kind in ("Text", "Label")),
        None,
    )
    if cursor_idx is None:
        return None
    for prop_name, items in consumers.items():
        for idx, key, _expr in items:
            if idx == cursor_idx and key == "text":
                return prop_name
    return None


def plan_line_plot_hover(
    mod: Module,
    layouts: dict[int, NodeLayout],
    names: dict[int, str],
) -> LinePlotHoverPlan | None:
    plot_idx = next(
        (
            i
            for i, n in enumerate(mod.nodes)
            if n.kind == "LinePlot" and n.properties.get("hoverEnabled")
        ),
        None,
    )
    if plot_idx is None:
        return None
    cursor_idx = next(
        (i for i, n in enumerate(mod.nodes) if n.id == "cursorLabel" and n.kind in ("Text", "Label")),
        None,
    )
    if cursor_idx is None:
        return None
    return LinePlotHoverPlan(
        plot_field=names[plot_idx],
        cursor_field=names[cursor_idx],
    )


def emit_line_plot_hover_fields(plan: LinePlotHoverPlan) -> list[str]:
    f = plan.plot_field
    return [
        f"    lv_obj_t * {f}_hit;",
        f"    lv_obj_t * {f}_cross_v;",
        f"    lv_obj_t * {f}_cross_h;",
    ]


def _cursor_idle_literal(mod: Module, cursor_text_prop: str | None) -> str:
    if cursor_text_prop:
        for prop in mod.module_properties:
            if prop.name == cursor_text_prop and prop.default is not None:
                return str(prop.default).replace("\\", "\\\\").replace('"', '\\"')
    return ""


def emit_line_plot_hover_callback(
    mod: Module,
    plan: LinePlotHoverPlan,
    cursor_text_prop: str | None = None,
) -> str:
    f = plan.plot_field
    idle = _cursor_idle_literal(mod, cursor_text_prop)
    released_body = "        qvgl_plot_clear_crosshair(&ui->" + f + "_plot);\n"
    if cursor_text_prop:
        released_body += f'        qvgl_{mod.module}_set_{cursor_text_prop}(ui, "{idle}");\n'
    elif plan.cursor_field:
        released_body += f'        qvgl_widget_set_text(ui->{plan.cursor_field}, "{idle}");\n'

    cursor_update = ""
    if cursor_text_prop:
        cursor_update = f"""    char ts[24];
    char ys[24];
    char buf[64];
    qvgl_plot_format_axis(t, ts, sizeof(ts));
    qvgl_plot_format_axis(y, ys, sizeof(ys));
    lv_snprintf(buf, sizeof(buf), "t=%s  y=%s", ts, ys);
    qvgl_{mod.module}_set_{cursor_text_prop}(ui, buf);
    qvgl_plot_set_crosshair(plot, t, y);
"""
    else:
        cursor_update = "    qvgl_plot_set_cursor(plot, t, y);\n"

    return f"""static void qvgl_{mod.module}_{f}_hover_cb(lv_event_t * e)
{{
    lv_event_code_t code = lv_event_get_code(e);
    if(code != LV_EVENT_PRESSING && code != LV_EVENT_PRESSED && code != LV_EVENT_RELEASED) return;
    qvgl_ui_{mod.module}_t * ui = lv_event_get_user_data(e);
    if(!ui) return;
    if(code == LV_EVENT_RELEASED) {{
{released_body}        return;
    }}
    lv_point_t p;
    lv_indev_get_point(lv_indev_active(), &p);
    lv_area_t a;
    lv_obj_get_coords(ui->{f}_hit, &a);
    int mx = p.x - a.x1;
    int my = p.y - a.y1;
    qvgl_plot_t * plot = &ui->{f}_plot;
    if(mx < 0 || my < 0 || mx > plot->chart_w || my > plot->chart_h) return;
    float x_span = plot->x_max - plot->x_min;
    float y_span = plot->y_max - plot->y_min;
    if(x_span < 1e-6f) x_span = 1.0f;
    if(y_span < 1e-6f) y_span = 1.0f;
    float t = plot->x_min + (float)mx / (float)plot->chart_w * x_span;
    float y = plot->y_max - (float)my / (float)plot->chart_h * y_span;
{cursor_update}}}
"""


def emit_line_plot_module_api(
    mod: Module,
    plot_plans: list[tuple[str, LinePlotEmitPlan]],
    hover: LinePlotHoverPlan | None,
    cursor_text_prop: str | None = None,
) -> tuple[str, str]:
    if not plot_plans:
        return "", ""

    decls: list[str] = []
    fns: list[str] = []
    for field, plan in plot_plans:
        decls.append(
            f"void qvgl_ui_{mod.module}_set_{field}_points("
            f"qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count);"
        )
        decls.append(
            f"void qvgl_ui_{mod.module}_set_{field}_domain("
            f"qvgl_ui_{mod.module}_t * ui, float x_min, float x_max, float y_min, float y_max);"
        )
        decls.append(
            f"void qvgl_ui_{mod.module}_apply_{field}_series("
            f"qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count);"
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_set_{field}_points(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count)
{{
    if(!ui) return;
    qvgl_plot_set_points(&ui->{field}_plot, pts, count);
}}
"""
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_set_{field}_domain(qvgl_ui_{mod.module}_t * ui, float x_min, float x_max, float y_min, float y_max)
{{
    if(!ui) return;
    qvgl_plot_set_domain(&ui->{field}_plot, x_min, x_max, y_min, y_max);
}}
"""
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_apply_{field}_series(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count)
{{
    if(!ui) return;
    qvgl_plot_apply_series(&ui->{field}_plot, pts, count, {_float_c_literal(plan.x_min)}, {_float_c_literal(plan.x_max)}, {_float_c_literal(plan.y_min)}, {_float_c_literal(plan.y_max)});
}}
"""
        )

    if hover:
        decls.append(
            f"void qvgl_ui_{mod.module}_set_plot_cursor(qvgl_ui_{mod.module}_t * ui, float t_sec, float y_val);"
        )
        f = hover.plot_field
        if cursor_text_prop:
            fns.append(
                f"""void qvgl_ui_{mod.module}_set_plot_cursor(qvgl_ui_{mod.module}_t * ui, float t_sec, float y_val)
{{
    if(!ui) return;
    char ts[24];
    char ys[24];
    char buf[64];
    qvgl_plot_format_axis(t_sec, ts, sizeof(ts));
    qvgl_plot_format_axis(y_val, ys, sizeof(ys));
    lv_snprintf(buf, sizeof(buf), "t=%s  y=%s", ts, ys);
    qvgl_{mod.module}_set_{cursor_text_prop}(ui, buf);
    qvgl_plot_set_crosshair(&ui->{f}_plot, t_sec, y_val);
}}
"""
            )
        else:
            fns.append(
                f"""void qvgl_ui_{mod.module}_set_plot_cursor(qvgl_ui_{mod.module}_t * ui, float t_sec, float y_val)
{{
    if(!ui) return;
    qvgl_plot_set_cursor(&ui->{f}_plot, t_sec, y_val);
}}
"""
            )

    if len(plot_plans) == 1:
        field, plan = plot_plans[0]
        decls.append(
            f"void qvgl_ui_{mod.module}_set_plot_points(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count);"
        )
        decls.append(
            f"void qvgl_ui_{mod.module}_set_plot_domain(qvgl_ui_{mod.module}_t * ui, float x_min, float x_max, float y_min, float y_max);"
        )
        decls.append(
            f"void qvgl_ui_{mod.module}_apply_plot_series(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count);"
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_set_plot_points(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count)
{{
    qvgl_ui_{mod.module}_set_{field}_points(ui, pts, count);
}}
"""
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_set_plot_domain(qvgl_ui_{mod.module}_t * ui, float x_min, float x_max, float y_min, float y_max)
{{
    qvgl_ui_{mod.module}_set_{field}_domain(ui, x_min, x_max, y_min, y_max);
}}
"""
        )
        fns.append(
            f"""void qvgl_ui_{mod.module}_apply_plot_series(qvgl_ui_{mod.module}_t * ui, const qvgl_plot_point_t * pts, size_t count)
{{
    qvgl_ui_{mod.module}_apply_{field}_series(ui, pts, count);
}}
"""
        )

    header = "\n".join(decls) + "\n"
    body = "\n".join(fns)
    return header, body


def emit_line_plot_resize_callback(mod: Module, field: str) -> str:
    pf = f"{field}_plot"
    return f"""static void qvgl_{mod.module}_{field}_resize_cb(lv_event_t * e)
{{
    if(lv_event_get_code(e) != LV_EVENT_SIZE_CHANGED) return;
    qvgl_ui_{mod.module}_t * ui = lv_event_get_user_data(e);
    if(!ui) return;
    qvgl_plot_relayout(&ui->{pf});
}}
"""


def emit_line_plot_create(
    mod: Module,
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    profile,
    rel_x: int,
    rel_y: int,
    hover: LinePlotHoverPlan | None = None,
    *,
    responsive: bool = False,
) -> list[str]:
    plan = plan_line_plot(node, lay)
    r = lay.rect
    pad_l = int(node.properties.get("padL", 52))
    pad_r = int(node.properties.get("padR", 10))
    pad_t = int(node.properties.get("padT", 10))
    pad_b = int(node.properties.get("padB", 30))
    line_color = str(node.properties.get("lineColor", "#ff4fc3f7"))
    plot_bg = str(node.properties.get("plotBg", "#ff0d0d0f"))
    grid_color = str(node.properties.get("gridColor", "#ff2a2b2f"))
    axis_color = str(node.properties.get("axisColor", "#ff3d3e42"))
    label_color = str(node.properties.get("labelColor", "#ff9aa0a6"))
    unit_muted = str(node.properties.get("unitMutedColor", "#ff6b7075"))
    grid_div = plan.grid_div
    tick_count = grid_div + 1
    y_unit = str(node.properties.get("yUnit", "A"))
    x_unit = str(node.properties.get("xUnit", "t (s)"))

    chart_x = plan.chart_x
    chart_y = plan.chart_y
    chart_w = plan.chart_w
    chart_h = plan.chart_h
    pf = f"{field}_plot"

    size_lines = (
        [
            f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
            f"    lv_obj_set_flex_grow(ui->{field}, 1);",
        ]
        if responsive
        else [
            f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
            f"    lv_obj_set_pos(ui->{field}, {rel_x}, {rel_y});",
        ]
    )

    lines = [
        f"    ui->{field} = lv_obj_create({parent});",
        f"    lv_obj_remove_style_all(ui->{field});",
        *size_lines,
        f"    lv_obj_set_style_bg_color(ui->{field}, {lv_color_hex_expr(plot_bg)}, 0);",
        f"    lv_obj_set_style_bg_opa(ui->{field}, LV_OPA_COVER, 0);",
        f"    lv_obj_clear_flag(ui->{field}, LV_OBJ_FLAG_SCROLLABLE);",
        f"    ui->{pf}.pad_l = {pad_l};",
        f"    ui->{pf}.pad_r = {pad_r};",
        f"    ui->{pf}.pad_t = {pad_t};",
        f"    ui->{pf}.pad_b = {pad_b};",
        f"    ui->{pf}.chart_x = {chart_x};",
        f"    ui->{pf}.chart_y = {chart_y};",
        f"    ui->{pf}.chart_w = {chart_w};",
        f"    ui->{pf}.chart_h = {chart_h};",
        f"    ui->{pf}.tick_count = {tick_count};",
        f"    ui->{pf}.chart = lv_chart_create(ui->{field});",
        f"    lv_obj_set_size(ui->{pf}.chart, {chart_w}, {chart_h});",
        f"    lv_obj_set_pos(ui->{pf}.chart, {chart_x}, {chart_y});",
        f"    lv_chart_set_type(ui->{pf}.chart, LV_CHART_TYPE_SCATTER);",
        f"    lv_chart_set_div_line_count(ui->{pf}.chart, {grid_div}, {grid_div});",
        f"    lv_obj_set_style_bg_color(ui->{pf}.chart, {lv_color_hex_expr(plot_bg)}, 0);",
        f"    lv_obj_set_style_bg_opa(ui->{pf}.chart, LV_OPA_COVER, 0);",
        f"    lv_obj_set_style_border_width(ui->{pf}.chart, 0, 0);",
        f"    lv_obj_set_style_line_color(ui->{pf}.chart, {lv_color_hex_expr(grid_color)}, LV_PART_MAIN);",
        f"    lv_obj_set_style_line_width(ui->{pf}.chart, 1, LV_PART_MAIN);",
    ]

    if plan.point_count > 0:
        lines += [
            f"    lv_chart_set_point_count(ui->{pf}.chart, {plan.point_count});",
            f"    ui->{pf}.series = lv_chart_add_series(ui->{pf}.chart, {lv_color_hex_expr(line_color)}, LV_CHART_AXIS_PRIMARY_Y);",
            f"    lv_obj_set_style_line_width(ui->{pf}.chart, 2, LV_PART_ITEMS);",
        ]
    else:
        lines.append(f"    lv_chart_set_point_count(ui->{pf}.chart, 0);")

    axis_font = lv_font_expr(profile, 10)
    unit_font = lv_font_expr(profile, 9)

    for i in range(tick_count):
        lines += [
            f"    ui->{pf}.x_labels[{i}] = lv_label_create(ui->{field});",
            f"    lv_obj_set_style_text_color(ui->{pf}.x_labels[{i}], {lv_color_hex_expr(label_color)}, 0);",
            f"    lv_obj_set_style_text_font(ui->{pf}.x_labels[{i}], {axis_font}, 0);",
            f"    ui->{pf}.y_labels[{i}] = lv_label_create(ui->{field});",
            f"    lv_obj_set_style_text_color(ui->{pf}.y_labels[{i}], {lv_color_hex_expr(label_color)}, 0);",
            f"    lv_obj_set_style_text_font(ui->{pf}.y_labels[{i}], {axis_font}, 0);",
        ]

    lines += [
        f"    ui->{pf}.x_unit_label = lv_label_create(ui->{field});",
        f'    lv_label_set_text(ui->{pf}.x_unit_label, "{x_unit}");',
        f"    lv_obj_set_style_text_color(ui->{pf}.x_unit_label, {lv_color_hex_expr(unit_muted)}, 0);",
        f"    lv_obj_set_style_text_font(ui->{pf}.x_unit_label, {unit_font}, 0);",
        f"    lv_obj_set_pos(ui->{pf}.x_unit_label, {chart_x + chart_w - 36}, {chart_y + chart_h + 4});",
    ]
    if y_unit:
        lines += [
            f"    ui->{pf}.y_unit_label = lv_label_create(ui->{field});",
            f'    lv_label_set_text(ui->{pf}.y_unit_label, "{y_unit}");',
            f"    lv_obj_set_style_text_color(ui->{pf}.y_unit_label, {lv_color_hex_expr(unit_muted)}, 0);",
            f"    lv_obj_set_style_text_font(ui->{pf}.y_unit_label, {unit_font}, 0);",
            f"    lv_obj_set_pos(ui->{pf}.y_unit_label, 2, {chart_y + 6});",
        ]

    lines += [
        f"    ui->{pf}.axis_bottom = lv_obj_create(ui->{field});",
        f"    lv_obj_remove_style_all(ui->{pf}.axis_bottom);",
        f"    lv_obj_set_size(ui->{pf}.axis_bottom, {chart_w}, 2);",
        f"    lv_obj_set_pos(ui->{pf}.axis_bottom, {chart_x}, {chart_y + chart_h - 1});",
        f"    lv_obj_set_style_bg_color(ui->{pf}.axis_bottom, {lv_color_hex_expr(axis_color)}, 0);",
        f"    lv_obj_set_style_bg_opa(ui->{pf}.axis_bottom, LV_OPA_COVER, 0);",
        f"    ui->{pf}.axis_left = lv_obj_create(ui->{field});",
        f"    lv_obj_remove_style_all(ui->{pf}.axis_left);",
        f"    lv_obj_set_size(ui->{pf}.axis_left, 2, {chart_h});",
        f"    lv_obj_set_pos(ui->{pf}.axis_left, {chart_x}, {chart_y});",
        f"    lv_obj_set_style_bg_color(ui->{pf}.axis_left, {lv_color_hex_expr(axis_color)}, 0);",
        f"    lv_obj_set_style_bg_opa(ui->{pf}.axis_left, LV_OPA_COVER, 0);",
        f"    qvgl_plot_set_domain(&ui->{pf}, {_float_c_literal(plan.x_min)}, {_float_c_literal(plan.x_max)}, {_float_c_literal(plan.y_min)}, {_float_c_literal(plan.y_max)});",
    ]

    if plan.point_count > 0:
        lines.append(
            f"    qvgl_plot_set_points(&ui->{pf}, qvgl_{field}_initial, {plan.point_count});"
        )

    if hover and hover.plot_field == field:
        cross_color = lv_color_hex_expr(str(node.properties.get("labelColor", "#ff9aa0a6")))
        lines += [
            f"    ui->{field}_hit = lv_obj_create(ui->{field});",
            f"    lv_obj_remove_style_all(ui->{field}_hit);",
            f"    lv_obj_set_size(ui->{field}_hit, {chart_w}, {chart_h});",
            f"    lv_obj_set_pos(ui->{field}_hit, {chart_x}, {chart_y});",
            f"    lv_obj_add_flag(ui->{field}_hit, LV_OBJ_FLAG_CLICKABLE);",
            f"    ui->{field}_cross_v = lv_obj_create(ui->{field});",
            f"    lv_obj_remove_style_all(ui->{field}_cross_v);",
            f"    lv_obj_set_style_bg_color(ui->{field}_cross_v, {cross_color}, 0);",
            f"    lv_obj_set_style_bg_opa(ui->{field}_cross_v, LV_OPA_COVER, 0);",
            f"    lv_obj_add_flag(ui->{field}_cross_v, LV_OBJ_FLAG_HIDDEN);",
            f"    ui->{pf}.cross_v = ui->{field}_cross_v;",
            f"    ui->{field}_cross_h = lv_obj_create(ui->{field});",
            f"    lv_obj_remove_style_all(ui->{field}_cross_h);",
            f"    lv_obj_set_style_bg_color(ui->{field}_cross_h, {cross_color}, 0);",
            f"    lv_obj_set_style_bg_opa(ui->{field}_cross_h, LV_OPA_COVER, 0);",
            f"    lv_obj_add_flag(ui->{field}_cross_h, LV_OBJ_FLAG_HIDDEN);",
            f"    ui->{pf}.cross_h = ui->{field}_cross_h;",
            f"    ui->{pf}.hit = ui->{field}_hit;",
            f"    lv_obj_add_event_cb(ui->{field}_hit, qvgl_{mod.module}_{field}_hover_cb, LV_EVENT_ALL, ui);",
        ]

    if responsive:
        lines += [
            f"    qvgl_plot_relayout(&ui->{pf});",
            f"    lv_obj_add_event_cb(ui->{field}, qvgl_{mod.module}_{field}_resize_cb, LV_EVENT_SIZE_CHANGED, ui);",
        ]

    return lines


def emit_line_plot_cursor_bind(hover: LinePlotHoverPlan, cursor_text_prop: str | None) -> str:
    if cursor_text_prop:
        return ""
    f = hover.plot_field
    return f"    ui->{f}_plot.cursor_label = ui->{hover.cursor_field};"


# Back-compat alias used by static_ui imports
def emit_line_plot_static(node: Node, field: str) -> list[str]:
    return emit_line_plot_initial_series(node, field)
