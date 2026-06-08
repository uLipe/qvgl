from __future__ import annotations

import re
from pathlib import Path

from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.emit_lvgl.conf import (
    collect_required_fonts,
    emit_qvgl_lv_conf,
    emit_qvgl_lvgl_config,
    emit_qvgl_sdkconfig_defaults,
    emit_qvgl_sources_cmake,
)
from qvglc.emit_lvgl.layout import layout_module
from qvglc.emit_lvgl.preview_shim import emit_preview_shim
from qvglc.ir.model import Module, Node
from qvglc.theme import resolve_theme_member
from qvglc.layout import NodeLayout
from qvglc.lvgl_probe.probe import LvglCapabilities

from .assets import collect_image_nodes, emit_assets
from .bindings_codegen import (
    emit_setter_body,
    property_consumers,
    setter_decl,
    struct_field_decl,
    struct_field_init,
)
from .emit_context import EmitContext
from .errors import EmitError
from .line_plot import (
    cursor_text_property,
    emit_line_plot_create,
    emit_line_plot_cursor_bind,
    emit_line_plot_hover_callback,
    emit_line_plot_hover_fields,
    emit_line_plot_module_api,
    emit_line_plot_resize_callback,
    emit_line_plot_static,
    emit_line_plot_struct_field,
    plan_line_plot,
    plan_line_plot_hover,
)
from .combo import (
    combo_initial_index,
    combo_model_items,
    combo_options_c_literal,
    emit_combo_create,
)
from .slider import (
    SliderEmitPlan,
    emit_slider_create,
    plan_slider,
    slider_initial,
)
from .responsive_layout import (
    anchor_margins,
    anchors_fill_parent,
    emit_flex_column,
    emit_flex_grow_row_child,
    emit_flex_row,
    emit_pct_fill,
    emit_tool_button_geometry,
    emit_widget_geometry,
    layout_fill_width,
    module_uses_responsive_layout,
)
from .widget_style import (
    emit_border,
    emit_enabled,
    emit_opacity_visible,
    image_layout,
    lv_font_expr,
)


def _snake(s: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
    return s.replace("-", "_")


def _field_name(node: Node, idx: int) -> str:
    if node.id:
        return _snake(node.id)
    return f"{node.kind.lower()}_{idx}"


def _text_literal(node: Node, mod: Module) -> str:
    text = node.properties.get("text", "")
    if isinstance(text, dict) and "binding" in text:
        expr = text["binding"]
        if expr.get("op") == "format":
            fmt = expr["args"][0].get("const", "%.1f")
            for prop in mod.module_properties:
                if prop.default is not None:
                    return fmt.replace("%.1f", f"{float(prop.default):.1f}").replace("%d", str(prop.default))
            return "0"
        if "sym" in expr:
            for prop in mod.module_properties:
                if prop.name == expr["sym"] and prop.default is not None:
                    return str(prop.default)
            return "0"
        return "..."
    return str(text)


_SIGNAL_EVENT = {
    "clicked": "LV_EVENT_CLICKED",
    "pressed": "LV_EVENT_PRESSED",
    "released": "LV_EVENT_RELEASED",
    "moved": "LV_EVENT_VALUE_CHANGED",
    "valueChanged": "LV_EVENT_VALUE_CHANGED",
    "activated": "LV_EVENT_VALUE_CHANGED",
}

_SLIDER_HANDLER_SIGNALS = frozenset({"moved", "valueChanged"})
_COMBO_HANDLER_SIGNALS = frozenset({"activated"})


def _handler_cb_name(mod: Module, field: str, signal: str) -> str:
    if signal == "clicked":
        return f"qvgl_{mod.module}_{field}_click_cb"
    return f"qvgl_{mod.module}_{field}_{signal}_cb"


def _handler_cbs_for(
    handlers: list,
    node_id: str,
    field: str,
    mod: Module,
    signals: frozenset[str],
) -> list[str]:
    out: list[str] = []
    for h in handlers:
        if h.node == node_id and h.signal in signals:
            out.append(_handler_cb_name(mod, field, h.signal))
    return out


def _with_style(node: Node, field: str, lines: list[str]) -> list[str]:
    var = f"ui->{field}"
    lines.extend(emit_opacity_visible(node, var))
    lines.extend(emit_enabled(node, var))
    return lines


def _rel_pos(mod: Module, layouts: dict[int, NodeLayout], idx: int) -> tuple[int, int]:
    lay = layouts[idx]
    node = mod.nodes[idx]
    if node.parent < 0:
        return lay.rect.x, lay.rect.y
    parent = layouts[node.parent].rect
    return lay.rect.x - parent.x, lay.rect.y - parent.y


def emit_static(
    mod: Module,
    caps: LvglCapabilities,
    out_dir: Path,
    ctx: EmitContext | None = None,
) -> list[Path]:
    if any(n.kind == "Arc" for n in mod.nodes):
        raise EmitError("modules with Arc nodes require hybrid emit")

    if caps.major < 9:
        raise EmitError(f"LVGL 9+ required, found {caps.version_string}")

    emit_ctx = ctx or EmitContext()
    profile = emit_ctx.resolve_profile(mod.profile)
    use_image = bool(collect_image_nodes(mod))
    fonts = collect_required_fonts(mod, profile)
    id_by_source: dict[str, tuple[str, int, int]] = {}
    assets_include = ""
    with_assets = False
    if use_image:
        if emit_ctx.asset_root is None:
            raise EmitError("Image nodes require asset_root (compile from .qml path)")
        _, id_by_source = emit_assets(mod, emit_ctx, out_dir)
        assets_include = f'#include "qvgl_{mod.module}_assets.h"\n'
        with_assets = True

    layouts = layout_module(mod)
    root = mod.nodes[mod.root]
    root_lay = layouts[mod.root]
    names = {idx: _field_name(node, idx) for idx, node in enumerate(mod.nodes)}
    names[mod.root] = "root"
    consumers = property_consumers(mod)
    bound_props = [p for p in mod.module_properties if consumers.get(p.name)]
    signal_handlers = [h for h in mod.handlers if h.signal in _SIGNAL_EVENT]
    handler_ids = {h.node for h in mod.handlers}
    hover_plan = plan_line_plot_hover(mod, layouts, names)
    cursor_text_prop = cursor_text_property(mod) if hover_plan else None
    responsive = module_uses_responsive_layout(mod)
    plot_plans: list[tuple[str, object]] = []
    slider_plans: dict[int, SliderEmitPlan] = {}

    fields: list[str] = []
    create: list[str] = []
    static_cbs: list[str] = []
    static_data: list[str] = []
    setter_fns: list[str] = []
    setter_decls: list[str] = []
    init_setters: list[str] = []

    for idx, node in enumerate(mod.nodes):
        if node.kind == "LinePlot":
            field = names[idx]
            static_data.extend(emit_line_plot_static(node, field))
            plot_plans.append((field, plan_line_plot(node, layouts[idx])))

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            fields.append("    lv_obj_t * root;")
        else:
            fields.append(f"    lv_obj_t * {names[idx]};")
        if node.kind == "LinePlot":
            fields.append(emit_line_plot_struct_field(names[idx]))
    if hover_plan:
        fields.extend(emit_line_plot_hover_fields(hover_plan))

    for prop in bound_props:
        fields.append(struct_field_decl(prop))

    create.extend(_emit_root(root, root_lay, names[mod.root], profile, responsive))

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            continue
        if node.kind == "Slider":
            slider_plans[idx] = plan_slider(node, slider_initial(node, mod, consumers))

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            continue
        lay = layouts[idx]
        rx, ry = _rel_pos(mod, layouts, idx)
        parent = f"ui->{names[node.parent]}"
        parent_node = mod.nodes[node.parent]
        create.extend(
            _emit_node(
                mod,
                idx,
                node,
                lay,
                names[idx],
                parent,
                parent_node,
                handler_ids,
                profile,
                id_by_source,
                rx,
                ry,
                hover_plan,
                responsive,
                slider_plans,
                mod.handlers,
            )
        )

    if responsive:
        for field, _ in plot_plans:
            static_cbs.append(emit_line_plot_resize_callback(mod, field))

    for h in signal_handlers:
        cb = h.handler
        field = names[next(i for i, n in enumerate(mod.nodes) if n.id == h.node)]
        event = _SIGNAL_EVENT[h.signal]
        cb_name = _handler_cb_name(mod, field, h.signal)
        static_cbs.append(
            f"""static void {cb_name}(lv_event_t * e)
{{
    if(lv_event_get_code(e) != {event}) return;
    {cb}();
}}
"""
        )

    prop_inits = [struct_field_init(p) for p in bound_props]
    for prop in bound_props:
        setter_decls.append(setter_decl(mod, prop))
        setter_fns.append(
            emit_setter_body(mod, prop, consumers[prop.name], names, {}, slider_plans)
        )
        init_setters.append(f"    qvgl_{mod.module}_set_{prop.name}(ui, ui->{prop.name});")

    plot_api_h = ""
    plot_api_c = ""
    plot_includes = ""
    if plot_plans:
        plot_includes = '#include "qvgl/qvgl_plot_lvgl.h"\n'
        plot_api_h, plot_api_c = emit_line_plot_module_api(
            mod, plot_plans, hover_plan, cursor_text_prop
        )
        plot_api_h = "\n" + plot_api_h
        if plot_api_c:
            plot_api_c += "\n"
    if hover_plan:
        static_cbs.append(emit_line_plot_hover_callback(mod, hover_plan, cursor_text_prop))
        bind = emit_line_plot_cursor_bind(hover_plan, cursor_text_prop)
        if bind:
            create.append(bind)

    mod_upper = mod.module.upper()
    pub_h = ""
    pub_path: Path | None = None
    if bound_props:
        pub_h = f"""#ifndef QVGL_{mod_upper}_H
#define QVGL_{mod_upper}_H

#include "ui_{mod.module}.h"

#ifdef __cplusplus
extern "C" {{
#endif

{chr(10).join(setter_decls)}

#ifdef __cplusplus
}}
#endif

#endif
"""
        pub_path = out_dir / f"qvgl_{mod.module}.h"
    ui_h = f"""#ifndef UI_{mod_upper}_H
#define UI_{mod_upper}_H

#include "lvgl.h"
#include "qvgl/qvgl_plot_lvgl.h"

#ifdef __cplusplus
extern "C" {{
#endif

typedef struct {{
{chr(10).join(fields)}
}} qvgl_ui_{mod.module}_t;

void qvgl_ui_{mod.module}_create(lv_obj_t * parent, qvgl_ui_{mod.module}_t * ui);
{plot_api_h}
#ifdef __cplusplus
}}
#endif

#endif
"""

    externs = "\n".join(f"extern void {h.handler}(void);" for h in signal_handlers)
    static_block = "\n".join(static_data)
    if static_block:
        static_block += "\n"
    pub_include = f'#include "qvgl_{mod.module}.h"\n' if bound_props else ""
    widget_include = '#include "qvgl/qvgl_widget.h"\n' if bound_props else ""
    extra_includes = ""
    if any(p.type == "str" for p in bound_props):
        extra_includes += "#include <string.h>\n"
    if any(p.type == "bool" for p in bound_props):
        extra_includes += "#include <stdbool.h>\n"
    ui_c = f"""#include "ui_{mod.module}.h"
{pub_include}{plot_includes}{assets_include}{widget_include}{extra_includes}{externs}

{static_block}{chr(10).join(static_cbs)}
{plot_api_c}
void qvgl_ui_{mod.module}_create(lv_obj_t * parent, qvgl_ui_{mod.module}_t * ui)
{{
    if(!ui) return;
{chr(10).join(prop_inits)}
{chr(10).join(create)}
{chr(10).join(init_setters)}
}}

{chr(10).join(setter_fns)}
"""

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        out_dir / f"ui_{mod.module}.h",
        out_dir / f"ui_{mod.module}.c",
        out_dir / "qvgl_lv_conf.h",
        out_dir / "qvgl_lvgl.config",
        out_dir / "qvgl_sdkconfig.defaults",
        out_dir / "qvgl_sources.cmake",
    ]
    paths[0].write_text(ui_h, encoding="utf-8")
    paths[1].write_text(ui_c, encoding="utf-8")
    paths[2].write_text(emit_qvgl_lv_conf(caps, fonts=fonts, use_image=use_image), encoding="utf-8")
    paths[3].write_text(emit_qvgl_lvgl_config(fonts=fonts, use_image=use_image), encoding="utf-8")
    paths[4].write_text(emit_qvgl_sdkconfig_defaults(fonts=fonts, use_image=use_image), encoding="utf-8")
    paths[5].write_text(
        emit_qvgl_sources_cmake(
            str(caps.lvgl_path).replace("\\", "/"),
            mod.module,
            with_assets=with_assets,
        ),
        encoding="utf-8",
    )
    if pub_path and pub_h:
        pub_path.write_text(pub_h, encoding="utf-8")
        paths.insert(2, pub_path)
    emit_preview_shim(
        mod,
        out_dir,
        bound_props,
        has_plot_cursor=hover_plan is not None,
        has_plot_api=bool(plot_plans),
        module_name=mod.module,
    )
    paths.extend([out_dir / "qvgl_preview_shim.h", out_dir / "qvgl_preview_shim.c"])
    if with_assets:
        paths.extend(
            [
                out_dir / f"qvgl_{mod.module}_assets.h",
                out_dir / f"qvgl_{mod.module}_assets.c",
            ]
        )
    return paths


def _emit_root(root: Node, lay: NodeLayout, field: str, profile, responsive: bool) -> list[str]:
    r = lay.rect
    size_lines = emit_pct_fill(field) if responsive else [f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});"]
    lines = [
        f"    ui->{field} = lv_obj_create(parent);",
        f"    lv_obj_remove_style_all(ui->{field});",
        *size_lines,
        f"    lv_obj_clear_flag(ui->{field}, LV_OBJ_FLAG_SCROLLABLE);",
    ]
    if root.kind == "Rectangle" and "color" in root.properties:
        lines += [
            f"    lv_obj_set_style_bg_color(ui->{field}, {lv_color_hex_expr(str(root.properties['color']))}, 0);",
            f"    lv_obj_set_style_bg_opa(ui->{field}, LV_OPA_COVER, 0);",
        ]
        radius = int(root.properties.get("radius", 0))
        if radius:
            lines.append(f"    lv_obj_set_style_radius(ui->{field}, {radius}, 0);")
    lines.extend(emit_border(root, f"ui->{field}"))
    return _with_style(root, field, lines)


def _emit_node(
    mod: Module,
    idx: int,
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    parent_node: Node,
    handler_ids: set[str],
    profile,
    id_by_source: dict[str, tuple[str, int, int]],
    rel_x: int,
    rel_y: int,
    hover_plan,
    responsive: bool,
    slider_plans: dict[int, SliderEmitPlan],
    handlers: list,
) -> list[str]:
    r = lay.rect
    if node.kind == "Rectangle":
        if responsive and anchors_fill_parent(node):
            geom = emit_pct_fill(field)
        else:
            geom = emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y)
        lines = [
            f"    ui->{field} = lv_obj_create({parent});",
            f"    lv_obj_remove_style_all(ui->{field});",
            *geom,
        ]
        if "color" in node.properties:
            lines += [
                f"    lv_obj_set_style_bg_color(ui->{field}, {lv_color_hex_expr(str(node.properties['color']))}, 0);",
                f"    lv_obj_set_style_bg_opa(ui->{field}, LV_OPA_COVER, 0);",
            ]
        radius = int(node.properties.get("radius", 0))
        if radius:
            lines.append(f"    lv_obj_set_style_radius(ui->{field}, {radius}, 0);")
        lines.extend(emit_border(node, f"ui->{field}"))
        return _with_style(node, field, lines)

    if node.kind == "Text":
        px = int(node.properties.get("font.pixelSize", 14))
        label = _text_literal(node, mod)
        color = node.properties.get("color", "#ffffffff")
        lines = [
            f"    ui->{field} = lv_label_create({parent});",
            f'    lv_label_set_text(ui->{field}, "{label}");',
            f"    lv_obj_set_style_text_color(ui->{field}, {lv_color_hex_expr(str(color))}, 0);",
            f"    lv_obj_set_style_text_font(ui->{field}, {lv_font_expr(profile, px)}, 0);",
        ]
        if responsive and parent_node.kind == "RowLayout" and layout_fill_width(node):
            lines.extend(emit_flex_grow_row_child(field))
        elif responsive and parent_node.kind == "ColumnLayout":
            lines.append(f"    lv_obj_set_width(ui->{field}, LV_PCT(100));")
        elif lay.align_center:
            lines.append(
                f"    lv_obj_align(ui->{field}, LV_ALIGN_CENTER, 0, {lay.align_center_offset_y});"
            )
        else:
            lines.extend(emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y))
        return _with_style(node, field, lines)

    if node.kind == "Image":
        src = str(node.properties["source"])
        aid, img_w, img_h = id_by_source[src]
        fill_mode = str(node.properties.get("fillMode", "Stretch"))
        box = image_layout(r, img_w, img_h, fill_mode)
        lines = [
            f"    ui->{field} = lv_image_create({parent});",
            f"    lv_image_set_src(ui->{field}, &qvgl_asset_{aid});",
        ]
        if responsive and anchors_fill_parent(node):
            lines += emit_pct_fill(field)
        else:
            lines += [
                f"    lv_obj_set_size(ui->{field}, {box.w}, {box.h});",
                f"    lv_obj_set_pos(ui->{field}, {box.x}, {box.y});",
            ]
        return _with_style(node, field, lines)

    if node.kind == "MouseArea":
        lines = [
            f"    ui->{field} = lv_obj_create({parent});",
            f"    lv_obj_remove_style_all(ui->{field});",
            *emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y),
            f"    lv_obj_add_flag(ui->{field}, LV_OBJ_FLAG_CLICKABLE);",
        ]
        if node.id:
            for h in mod.handlers:
                if h.node != node.id or h.signal not in _SIGNAL_EVENT:
                    continue
                event = _SIGNAL_EVENT[h.signal]
                cb_name = _handler_cb_name(mod, field, h.signal)
                lines.append(
                    f"    lv_obj_add_event_cb(ui->{field}, {cb_name}, {event}, NULL);"
                )
        return _with_style(node, field, lines)

    if node.kind in ("ColumnLayout", "RowLayout"):
        spacing = int(node.properties.get("spacing", 0))
        if responsive:
            if node.kind == "ColumnLayout" and anchors_fill_parent(node):
                geom = emit_pct_fill(field)
                flex = emit_flex_column(field, spacing, anchor_margins(node))
            elif node.kind == "RowLayout":
                geom = [
                    f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
                    f"    lv_obj_set_height(ui->{field}, LV_SIZE_CONTENT);",
                ]
                flex = emit_flex_row(field, spacing)
            else:
                geom = [f"    lv_obj_set_width(ui->{field}, LV_PCT(100));"]
                flex = emit_flex_column(field, spacing, (0, 0, 0, 0))
        else:
            geom = [
                f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
                f"    lv_obj_set_pos(ui->{field}, {rel_x}, {rel_y});",
            ]
            flex = []
        lines = [
            f"    ui->{field} = lv_obj_create({parent});",
            f"    lv_obj_remove_style_all(ui->{field});",
            *geom,
            *flex,
            f"    lv_obj_clear_flag(ui->{field}, LV_OBJ_FLAG_SCROLLABLE);",
        ]
        return _with_style(node, field, lines)

    if node.kind == "LinePlot":
        return _with_style(
            node,
            field,
            emit_line_plot_create(
                mod,
                node,
                lay,
                field,
                parent,
                profile,
                rel_x,
                rel_y,
                hover=hover_plan,
                responsive=responsive,
            ),
        )

    if node.kind == "Slider":
        plan = slider_plans[idx]
        handler_cbs = (
            _handler_cbs_for(handlers, node.id, field, mod, _SLIDER_HANDLER_SIGNALS)
            if node.id
            else []
        )
        if responsive and parent_node.kind == "ColumnLayout":
            geom = [
                f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
                f"    lv_obj_set_height(ui->{field}, {max(r.h, 40)});",
            ]
        else:
            geom = emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y)
        return _with_style(
            node,
            field,
            emit_slider_create(field, parent, plan, geom, handler_cbs=handler_cbs),
        )

    if node.kind == "Switch":
        checked = bool(node.properties.get("checked", False))
        if isinstance(node.properties.get("checked"), dict):
            checked = False
        lines = [
            f"    ui->{field} = lv_switch_create({parent});",
            *emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y),
        ]
        if checked:
            lines.append(f"    lv_obj_add_state(ui->{field}, LV_STATE_CHECKED);")
        if node.id and node.id in handler_ids:
            cb_name = _handler_cb_name(mod, field, "clicked")
            lines.append(
                f"    lv_obj_add_event_cb(ui->{field}, {cb_name}, LV_EVENT_CLICKED, NULL);"
            )
        return _with_style(node, field, lines)

    if node.kind == "CheckBox":
        label = _text_literal(node, mod)
        checked = bool(node.properties.get("checked", False))
        if isinstance(node.properties.get("checked"), dict):
            checked = False
        color = node.properties.get("color", "#ffffffff")
        px = int(node.properties.get("font.pixelSize", 14))
        lines = [
            f"    ui->{field} = lv_checkbox_create({parent});",
            *emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y),
            f'    lv_checkbox_set_text(ui->{field}, "{label}");',
            f"    lv_obj_set_style_text_color(ui->{field}, {lv_color_hex_expr(str(color))}, 0);",
            f"    lv_obj_set_style_text_font(ui->{field}, {lv_font_expr(profile, px)}, 0);",
        ]
        if checked:
            lines.append(f"    lv_obj_add_state(ui->{field}, LV_STATE_CHECKED);")
        if node.id and node.id in handler_ids:
            cb_name = _handler_cb_name(mod, field, "clicked")
            lines.append(
                f"    lv_obj_add_event_cb(ui->{field}, {cb_name}, LV_EVENT_CLICKED, NULL);"
            )
        return _with_style(node, field, lines)

    if node.kind in ("ToolButton", "Button"):
        px = int(node.properties.get("font.pixelSize", 14))
        label = _text_literal(node, mod)
        color = node.properties.get("color", "#ffe0e0e0")
        lines = [
            f"    ui->{field} = lv_button_create({parent});",
            *emit_tool_button_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y),
        ]
        if node.kind == "Button":
            primary = resolve_theme_member(profile, "primary")
            lines.extend(
                [
                    f"    lv_obj_set_style_bg_color(ui->{field}, {lv_color_hex_expr(primary)}, 0);",
                    f"    lv_obj_set_style_bg_opa(ui->{field}, LV_OPA_COVER, 0);",
                    f"    lv_obj_set_style_radius(ui->{field}, 4, 0);",
                    f"    lv_obj_set_style_shadow_width(ui->{field}, 0, 0);",
                    f"    lv_obj_set_style_border_width(ui->{field}, 0, 0);",
                ]
            )
        else:
            lines.extend(
                [
                    f"    lv_obj_set_style_bg_opa(ui->{field}, LV_OPA_TRANSP, 0);",
                    f"    lv_obj_set_style_shadow_width(ui->{field}, 0, 0);",
                    f"    lv_obj_set_style_border_width(ui->{field}, 0, 0);",
                    f"    lv_obj_set_style_pad_all(ui->{field}, 0, 0);",
                ]
            )
        lines.extend(
            [
                f"    {{",
                f"        lv_obj_t * btn_label = lv_label_create(ui->{field});",
                f'        lv_label_set_text(btn_label, "{label}");',
                f"        lv_obj_set_style_text_color(btn_label, {lv_color_hex_expr(str(color))}, 0);",
                f"        lv_obj_set_style_text_font(btn_label, {lv_font_expr(profile, px)}, 0);",
                f"        lv_obj_center(btn_label);",
                f"    }}",
            ]
        )
        if node.id and node.id in handler_ids:
            lines.append(
                f"    lv_obj_add_event_cb(ui->{field}, qvgl_{mod.module}_{field}_click_cb, LV_EVENT_CLICKED, NULL);"
            )
        return _with_style(node, field, lines)

    if node.kind == "ComboBox":
        px = int(node.properties.get("font.pixelSize", 14))
        items = combo_model_items(node)
        options = combo_options_c_literal(items)
        selected = combo_initial_index(node, mod)
        if selected < 0:
            selected = 0
        if selected >= len(items):
            selected = max(0, len(items) - 1)
        handler_cbs = (
            _handler_cbs_for(handlers, node.id, field, mod, _COMBO_HANDLER_SIGNALS)
            if node.id
            else []
        )
        if responsive and parent_node.kind in ("ColumnLayout", "RowLayout"):
            geom = [
                f"    lv_obj_set_width(ui->{field}, LV_PCT(100));",
                f"    lv_obj_set_height(ui->{field}, {max(r.h, 40)});",
            ]
        else:
            geom = emit_widget_geometry(field, parent_node, responsive, r.w, r.h, rel_x, rel_y)
        lines = emit_combo_create(
            field,
            parent,
            geom,
            options=options,
            selected=selected,
            handler_cbs=handler_cbs,
        )
        lines.append(
            f"    lv_obj_set_style_text_font(ui->{field}, {lv_font_expr(profile, px)}, 0);"
        )
        return _with_style(node, field, lines)

    raise EmitError(f"static emit unsupported node kind: {node.kind}")
