from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from qvglc.emit_lvgl.arc_anim import ARC_ANIM_STATIC_CB
from qvglc.emit_lvgl.arc_gauge import (
    ArcGaugePlan,
    emit_arc_gauge_init,
    f32_scale_for_range,
    plan_arc_gauge,
)
from qvglc.emit_lvgl.arc_scale import arc_wants_scale, emit_arc_scale
from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.emit_lvgl.conf import (
    collect_required_fonts,
    emit_qvgl_lv_conf,
    emit_qvgl_lvgl_config,
    emit_qvgl_sources_cmake,
)
from qvglc.emit_lvgl.layout import layout_module
from qvglc.emit_lvgl.preview_shim import emit_preview_shim
from qvglc.ir.model import Module, ModuleProperty, Node
from qvglc.layout import NodeLayout
from qvglc.lvgl_probe.probe import LvglCapabilities

from .assets import collect_image_nodes, emit_assets
from .bindings_codegen import emit_setter_body, property_consumers
from .emit_context import EmitContext
from .errors import EmitError
from .static_ui import _emit_root, _text_literal, _with_style
from .widget_style import emit_border, image_layout, lv_font_expr


def _snake(s: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
    return s.replace("-", "_")


def _field_name(node: Node, idx: int) -> str:
    if node.id:
        return _snake(node.id)
    return f"{node.kind.lower()}_{idx}"


def _prop_default(prop: ModuleProperty) -> float:
    if prop.default is None:
        return 0.0
    return float(prop.default)


def _plan_arc(node: Node, initial: float) -> ArcGaugePlan:
    props = node.properties
    scale = f32_scale_for_range(float(props["minValue"]), float(props["maxValue"]))
    anim_ms = int(props.get("valueAnimationDuration", 0))
    return plan_arc_gauge(
        from_deg=float(props["from"]),
        to_deg=float(props["to"]),
        min_value=float(props["minValue"]),
        max_value=float(props["maxValue"]),
        line_width=int(props.get("lineWidth", 12)),
        color=str(props["color"]),
        initial_value=initial,
        scale=scale,
        value_anim_ms=anim_ms,
    )


def _arc_initial(node: Node, mod: Module, consumers: dict[str, list]) -> float:
    value = node.properties.get("value")
    if isinstance(value, dict) and "binding" in value:
        sym = value["binding"].get("sym")
        if sym:
            for prop in mod.module_properties:
                if prop.name == sym:
                    return _prop_default(prop)
    for prop in mod.module_properties:
        if consumers.get(prop.name):
            return _prop_default(prop)
    return 0.0


def _emit_arc(
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    plan: ArcGaugePlan,
) -> list[str]:
    r = lay.rect
    return [
        f"    ui->{field} = lv_arc_create({parent});",
        f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
        f"    lv_obj_set_pos(ui->{field}, {r.x}, {r.y});",
        *emit_arc_gauge_init(f"ui->{field}", plan),
    ]


def _emit_text_hybrid(
    mod: Module,
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    profile,
) -> list[str]:
    r = lay.rect
    px = int(node.properties.get("font.pixelSize", 14))
    label = _text_literal(node, mod)
    color = node.properties.get("color", "#ffffffff")
    lines = [
        f"    ui->{field} = lv_label_create({parent});",
        f'    lv_label_set_text(ui->{field}, "{label}");',
        f"    lv_obj_set_style_text_color(ui->{field}, {lv_color_hex_expr(str(color))}, 0);",
        f"    lv_obj_set_style_text_font(ui->{field}, {lv_font_expr(profile, px)}, 0);",
    ]
    if lay.align_center:
        lines.append(
            f"    lv_obj_align(ui->{field}, LV_ALIGN_CENTER, 0, {lay.align_center_offset_y});"
        )
    else:
        lines += [
            f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
            f"    lv_obj_set_pos(ui->{field}, {r.x}, {r.y});",
        ]
    return _with_style(node, field, lines)


def _emit_image(
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    id_by_source: dict[str, tuple[str, int, int]],
) -> list[str]:
    r = lay.rect
    src = str(node.properties["source"])
    aid, img_w, img_h = id_by_source[src]
    fill_mode = str(node.properties.get("fillMode", "Stretch"))
    box = image_layout(r, img_w, img_h, fill_mode)
    lines = [
        f"    ui->{field} = lv_image_create({parent});",
        f"    lv_image_set_src(ui->{field}, &qvgl_asset_{aid});",
        f"    lv_obj_set_size(ui->{field}, {box.w}, {box.h});",
        f"    lv_obj_set_pos(ui->{field}, {box.x}, {box.y});",
    ]
    return _with_style(node, field, lines)


def _emit_rectangle(
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
) -> list[str]:
    r = lay.rect
    lines = [
        f"    ui->{field} = lv_obj_create({parent});",
        f"    lv_obj_remove_style_all(ui->{field});",
        f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
        f"    lv_obj_set_pos(ui->{field}, {r.x}, {r.y});",
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


def _emit_mouse_area(
    mod: Module,
    node: Node,
    lay: NodeLayout,
    field: str,
    parent: str,
    handler_ids: set[str],
) -> list[str]:
    r = lay.rect
    lines = [
        f"    ui->{field} = lv_obj_create({parent});",
        f"    lv_obj_remove_style_all(ui->{field});",
        f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
        f"    lv_obj_set_pos(ui->{field}, {r.x}, {r.y});",
        f"    lv_obj_add_flag(ui->{field}, LV_OBJ_FLAG_CLICKABLE);",
    ]
    if node.id and node.id in handler_ids:
        lines.append(
            f"    lv_obj_add_event_cb(ui->{field}, qvgl_{mod.module}_{field}_click_cb, LV_EVENT_CLICKED, NULL);"
        )
    return _with_style(node, field, lines)


def emit_hybrid(
    mod: Module,
    caps: LvglCapabilities,
    out_dir: Path,
    ctx: EmitContext | None = None,
) -> list[Path]:
    caps.require_arc_gauge()
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
    names = {idx: _field_name(node, idx) for idx, node in enumerate(mod.nodes)}
    names[mod.root] = "root"
    consumers = property_consumers(mod)
    bound_props = [p for p in mod.module_properties if consumers.get(p.name)]
    click_handlers = [h for h in mod.handlers if h.signal == "clicked"]
    handler_ids = {h.node for h in mod.handlers}
    arc_plans: dict[int, ArcGaugePlan] = {}
    arc_scale_fields: dict[int, str] = {}

    fields: list[str] = []
    create: list[str] = []
    static_cbs: list[str] = []

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            fields.append("    lv_obj_t * root;")
        else:
            fields.append(f"    lv_obj_t * {names[idx]};")
            if node.kind == "Arc" and arc_wants_scale(node):
                scale_name = f"{names[idx]}_scale"
                arc_scale_fields[idx] = scale_name
                fields.append(f"    lv_obj_t * {scale_name};")

    for prop in bound_props:
        fields.append(f"    float {prop.name};")

    create.extend(_emit_root(mod.nodes[mod.root], layouts[mod.root], names[mod.root], profile))

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            continue
        lay = layouts[idx]
        field = names[idx]
        parent = f"ui->{names[node.parent]}"

        if node.kind == "Rectangle":
            create.extend(_emit_rectangle(node, lay, field, parent))
        elif node.kind == "Arc":
            initial = _arc_initial(node, mod, consumers)
            plan = _plan_arc(node, initial)
            arc_plans[idx] = plan
            if idx in arc_scale_fields:
                create.extend(
                    emit_arc_scale(node, lay, arc_scale_fields[idx], parent, plan)
                )
            create.extend(_emit_arc(node, lay, field, parent, plan))
        elif node.kind == "Text":
            create.extend(_emit_text_hybrid(mod, node, lay, field, parent, profile))
        elif node.kind == "Image":
            create.extend(_emit_image(node, lay, field, parent, id_by_source))
        elif node.kind == "MouseArea":
            create.extend(_emit_mouse_area(mod, node, lay, field, parent, handler_ids))
        elif node.kind == "Item":
            create.extend(
                _with_style(
                    node,
                    field,
                    [
                        f"    ui->{field} = lv_obj_create({parent});",
                        f"    lv_obj_remove_style_all(ui->{field});",
                        f"    lv_obj_set_size(ui->{field}, {lay.rect.w}, {lay.rect.h});",
                        f"    lv_obj_set_pos(ui->{field}, {lay.rect.x}, {lay.rect.y});",
                        f"    lv_obj_clear_flag(ui->{field}, LV_OBJ_FLAG_SCROLLABLE);",
                    ],
                )
            )
        else:
            raise EmitError(f"hybrid emit unsupported node kind: {node.kind}")

    if any(p.value_anim_ms > 0 for p in arc_plans.values()):
        static_cbs.append(ARC_ANIM_STATIC_CB)

    for h in click_handlers:
        field = names[next(i for i, n in enumerate(mod.nodes) if n.id == h.node)]
        static_cbs.append(
            f"""static void qvgl_{mod.module}_{field}_click_cb(lv_event_t * e)
{{
    if(lv_event_get_code(e) != LV_EVENT_CLICKED) return;
    {h.handler}();
}}
"""
        )

    setter_fns: list[str] = []
    setter_decls: list[str] = []
    init_setters: list[str] = []
    for prop in bound_props:
        setter_decls.append(
            f"void qvgl_{mod.module}_set_{prop.name}(qvgl_ui_{mod.module}_t * ui, float {prop.name});"
        )
        setter_fns.append(
            emit_setter_body(mod, prop.name, consumers[prop.name], names, arc_plans)
        )
        init_setters.append(f"    qvgl_{mod.module}_set_{prop.name}(ui, ui->{prop.name});")

    prop_inits = [f"    ui->{p.name} = {_prop_default(p):.1f}f;" for p in bound_props]

    mod_upper = mod.module.upper()
    ui_h = f"""#ifndef UI_{mod_upper}_H
#define UI_{mod_upper}_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {{
#endif

typedef struct {{
{chr(10).join(fields)}
}} qvgl_ui_{mod.module}_t;

void qvgl_ui_{mod.module}_create(lv_obj_t * parent, qvgl_ui_{mod.module}_t * ui);

#ifdef __cplusplus
}}
#endif

#endif
"""

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

    externs = "\n".join(f"extern void {h.handler}(void);" for h in click_handlers)
    pub_include = f'#include "qvgl_{mod.module}.h"\n' if bound_props else ""
    ui_c = f"""#include "ui_{mod.module}.h"
{pub_include}{assets_include}#include <math.h>

{externs}

{chr(10).join(static_cbs)}
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
        out_dir / "qvgl_sources.cmake",
    ]
    paths[0].write_text(ui_h, encoding="utf-8")
    paths[1].write_text(ui_c, encoding="utf-8")
    paths[2].write_text(emit_qvgl_lv_conf(caps, fonts=fonts, use_image=use_image), encoding="utf-8")
    paths[3].write_text(emit_qvgl_lvgl_config(fonts=fonts, use_image=use_image), encoding="utf-8")
    paths[4].write_text(
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

    emit_preview_shim(mod, out_dir, bound_props)
    paths.extend([out_dir / "qvgl_preview_shim.h", out_dir / "qvgl_preview_shim.c"])
    if with_assets:
        paths.extend(
            [
                out_dir / f"qvgl_{mod.module}_assets.h",
                out_dir / f"qvgl_{mod.module}_assets.c",
            ]
        )
    return paths
