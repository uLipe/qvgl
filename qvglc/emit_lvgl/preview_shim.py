from __future__ import annotations

from pathlib import Path

from qvglc.ir.model import Module, ModuleProperty


def _emit_apply_cases(mod: Module, props: list[ModuleProperty]) -> list[str]:
    cases: list[str] = []
    for prop in props:
        if prop.type in ("f32", "f64"):
            cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f"        qvgl_{mod.module}_set_{prop.name}(ui, (float)strtod(value, NULL));\n"
                f"        return 0;\n"
                f"    }}"
            )
        elif prop.type == "i32":
            cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f"        qvgl_{mod.module}_set_{prop.name}(ui, (int32_t)strtol(value, NULL, 10));\n"
                f"        return 0;\n"
                f"    }}"
            )
        elif prop.type == "bool":
            cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f'        bool v = (strcmp(value, "1") == 0 || strcmp(value, "true") == 0\n'
                f'                  || strcmp(value, "True") == 0 || strcmp(value, "TRUE") == 0);\n'
                f"        qvgl_{mod.module}_set_{prop.name}(ui, v);\n"
                f"        return 0;\n"
                f"    }}"
            )
        elif prop.type == "str":
            cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f"        qvgl_{mod.module}_set_{prop.name}(ui, value);\n"
                f"        return 0;\n"
                f"    }}"
            )
    return cases


def emit_preview_shim(
    mod: Module,
    out_dir: Path,
    bound_props: list[ModuleProperty] | None = None,
    *,
    has_plot_cursor: bool = False,
    has_plot_api: bool = False,
    module_name: str | None = None,
) -> None:
    root = mod.nodes[mod.root]
    w = int(root.properties.get("width", 400))
    h = int(root.properties.get("height", 400))
    name = module_name or mod.module
    ui_type = f"qvgl_ui_{name}_t"
    props = bound_props or []
    float_props = [p for p in props if p.type in ("f32", "f64")]

    if has_plot_cursor:
        plot_cursor_decl = (
            "\nvoid qvgl_preview_set_plot_cursor(qvgl_preview_ui_t * ui, float t_sec, float y_val);\n"
        )
        plot_cursor_fn = f"""void qvgl_preview_set_plot_cursor(qvgl_preview_ui_t * ui, float t_sec, float y_val)
{{
    if(!ui) return;
    qvgl_ui_{name}_set_plot_cursor(ui, t_sec, y_val);
}}
"""
    else:
        plot_cursor_decl = (
            "\nvoid qvgl_preview_set_plot_cursor(qvgl_preview_ui_t * ui, float t_sec, float y_val);\n"
        )
        plot_cursor_fn = """void qvgl_preview_set_plot_cursor(qvgl_preview_ui_t * ui, float t_sec, float y_val)
{
    (void)ui;
    (void)t_sec;
    (void)y_val;
}
"""

    if has_plot_api:
        plot_points_decl = (
            "\nvoid qvgl_preview_set_plot_points(qvgl_preview_ui_t * ui, const qvgl_plot_point_t * pts, size_t count);\n"
        )
        plot_points_fn = f"""void qvgl_preview_set_plot_points(qvgl_preview_ui_t * ui, const qvgl_plot_point_t * pts, size_t count)
{{
    if(!ui) return;
    qvgl_ui_{name}_set_plot_points(ui, pts, count);
}}
"""
    else:
        plot_points_decl = (
            "\nvoid qvgl_preview_set_plot_points(qvgl_preview_ui_t * ui, const qvgl_plot_point_t * pts, size_t count);\n"
        )
        plot_points_fn = """void qvgl_preview_set_plot_points(qvgl_preview_ui_t * ui, const qvgl_plot_point_t * pts, size_t count)
{
    (void)ui;
    (void)pts;
    (void)count;
}
"""

    extra_include = ""
    if props:
        extra_include += f'#include "qvgl_{name}.h"\n'
    if has_plot_api:
        extra_include += '#include "qvgl/qvgl_plot.h"\n'

    if props:
        float_cases = []
        for prop in float_props:
            float_cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f"        qvgl_{name}_set_{prop.name}(ui, value);\n"
                f"        return 0;\n"
                f"    }}"
            )
        set_fn = f"""int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value)
{{
    if(!ui || !name) return -1;
{chr(10).join(float_cases)}
    return -1;
}}
"""
        apply_cases = _emit_apply_cases(mod, props)
        apply_fn = f"""int qvgl_preview_apply_property(qvgl_preview_ui_t * ui, const char * name, const char * value)
{{
    if(!ui || !name || !value) return -1;
{chr(10).join(apply_cases)}
    return -1;
}}
"""
        prop_enum = "\n".join(
            f'    case {i}: return "{p.name}";' for i, p in enumerate(props)
        )
        count_fn = f"""uint32_t qvgl_preview_property_count(void)
{{
    return {len(props)};
}}

const char * qvgl_preview_property_name(uint32_t index)
{{
    switch(index) {{
{prop_enum}
    default: return NULL;
    }}
}}
"""
        sync_fn = """void qvgl_preview_ui_sync(qvgl_preview_ui_t * ui)
{
    (void)ui;
}
"""
        apply_decl = "\nint qvgl_preview_apply_property(qvgl_preview_ui_t * ui, const char * name, const char * value);\n"
    else:
        set_fn = """int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value)
{
    (void)ui;
    (void)name;
    (void)value;
    return -1;
}
"""
        apply_fn = """int qvgl_preview_apply_property(qvgl_preview_ui_t * ui, const char * name, const char * value)
{
    (void)ui;
    (void)name;
    (void)value;
    return -1;
}
"""
        count_fn = """uint32_t qvgl_preview_property_count(void)
{
    return 0;
}

const char * qvgl_preview_property_name(uint32_t index)
{
    (void)index;
    return NULL;
}
"""
        sync_fn = """void qvgl_preview_ui_sync(qvgl_preview_ui_t * ui)
{
    (void)ui;
}
"""
        apply_decl = "\nint qvgl_preview_apply_property(qvgl_preview_ui_t * ui, const char * name, const char * value);\n"

    header = f"""#ifndef QVGL_PREVIEW_SHIM_H
#define QVGL_PREVIEW_SHIM_H

#include "lvgl.h"
#include <stddef.h>
#include <stdint.h>

#include "ui_{name}.h"
#include "qvgl/qvgl_plot.h"

typedef {ui_type} qvgl_preview_ui_t;

void qvgl_preview_ui_create(lv_obj_t * parent, qvgl_preview_ui_t * ui);
void qvgl_preview_ui_sync(qvgl_preview_ui_t * ui);
int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value);
{apply_decl}uint32_t qvgl_preview_property_count(void);
const char * qvgl_preview_property_name(uint32_t index);
int32_t qvgl_preview_width(void);
int32_t qvgl_preview_height(void);
const char * qvgl_preview_title(void);
{plot_cursor_decl}{plot_points_decl}
#endif
"""

    source = f"""#include "qvgl_preview_shim.h"
{extra_include}
#include <stdlib.h>
#include <string.h>

void qvgl_preview_ui_create(lv_obj_t * parent, qvgl_preview_ui_t * ui)
{{
    qvgl_ui_{name}_create(parent, ui);
}}

{sync_fn}
{set_fn}
{apply_fn}
{count_fn}

int32_t qvgl_preview_width(void)
{{
    return {w};
}}

int32_t qvgl_preview_height(void)
{{
    return {h};
}}

const char * qvgl_preview_title(void)
{{
    return "QVGL {name}";
}}

{plot_cursor_fn}
{plot_points_fn}"""

    (out_dir / "qvgl_preview_shim.h").write_text(header, encoding="utf-8")
    (out_dir / "qvgl_preview_shim.c").write_text(source, encoding="utf-8")
