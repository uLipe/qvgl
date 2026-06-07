from __future__ import annotations

import re
from pathlib import Path

from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.emit_lvgl.conf import (
    collect_required_fonts,
    emit_qvgl_lv_conf,
    emit_qvgl_lvgl_config,
    emit_qvgl_sources_cmake,
)
from qvglc.emit_lvgl.layout import layout_module
from qvglc.emit_lvgl.preview_shim import emit_preview_shim
from qvglc.ir.model import Module, Node
from qvglc.layout import NodeLayout
from qvglc.lvgl_probe.probe import LvglCapabilities

from .assets import collect_image_nodes, emit_assets
from .emit_context import EmitContext
from .errors import EmitError
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


def _with_style(node: Node, field: str, lines: list[str]) -> list[str]:
    var = f"ui->{field}"
    lines.extend(emit_opacity_visible(node, var))
    lines.extend(emit_enabled(node, var))
    return lines


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
    click_handlers = [h for h in mod.handlers if h.signal == "clicked"]
    handler_ids = {h.node for h in mod.handlers}

    fields: list[str] = []
    create: list[str] = []
    static_cbs: list[str] = []

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            fields.append("    lv_obj_t * root;")
        else:
            fields.append(f"    lv_obj_t * {names[idx]};")

    create.extend(_emit_root(root, root_lay, names[mod.root], profile))

    for idx, node in enumerate(mod.nodes):
        if idx == mod.root:
            continue
        lay = layouts[idx]
        parent = f"ui->{names[node.parent]}"
        create.extend(
            _emit_node(
                mod,
                idx,
                node,
                lay,
                names[idx],
                parent,
                handler_ids,
                profile,
                id_by_source,
            )
        )

    for h in click_handlers:
        cb = h.handler
        field = names[next(i for i, n in enumerate(mod.nodes) if n.id == h.node)]
        static_cbs.append(
            f"""static void qvgl_{mod.module}_{field}_click_cb(lv_event_t * e)
{{
    if(lv_event_get_code(e) != LV_EVENT_CLICKED) return;
    {cb}();
}}
"""
        )

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

    externs = "\n".join(f"extern void {h.handler}(void);" for h in click_handlers)
    ui_c = f"""#include "ui_{mod.module}.h"
{assets_include}{externs}

{chr(10).join(static_cbs)}
void qvgl_ui_{mod.module}_create(lv_obj_t * parent, qvgl_ui_{mod.module}_t * ui)
{{
    if(!ui) return;
{chr(10).join(create)}
}}
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
    emit_preview_shim(mod, out_dir)
    paths.extend([out_dir / "qvgl_preview_shim.h", out_dir / "qvgl_preview_shim.c"])
    if with_assets:
        paths.extend(
            [
                out_dir / f"qvgl_{mod.module}_assets.h",
                out_dir / f"qvgl_{mod.module}_assets.c",
            ]
        )
    return paths


def _emit_root(root: Node, lay: NodeLayout, field: str, profile) -> list[str]:
    r = lay.rect
    lines = [
        f"    ui->{field} = lv_obj_create(parent);",
        f"    lv_obj_remove_style_all(ui->{field});",
        f"    lv_obj_set_size(ui->{field}, {r.w}, {r.h});",
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
    handler_ids: set[str],
    profile,
    id_by_source: dict[str, tuple[str, int, int]],
) -> list[str]:
    r = lay.rect
    if node.kind == "Rectangle":
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

    if node.kind == "Image":
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

    if node.kind == "MouseArea":
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

    raise EmitError(f"static emit unsupported node kind: {node.kind}")
