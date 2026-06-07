from __future__ import annotations

from pathlib import Path

from qvglc.ir.model import Module, ModuleProperty


def emit_preview_shim(
    mod: Module,
    out_dir: Path,
    bound_props: list[ModuleProperty] | None = None,
) -> None:
    root = mod.nodes[mod.root]
    w = int(root.properties.get("width", 400))
    h = int(root.properties.get("height", 400))
    name = mod.module
    ui_type = f"qvgl_ui_{name}_t"
    props = bound_props or []

    extra_include = f'#include "qvgl_{name}.h"\n' if props else ""

    if props:
        cases = []
        for prop in props:
            cases.append(
                f'    if(strcmp(name, "{prop.name}") == 0) {{\n'
                f"        qvgl_{name}_set_{prop.name}(ui, value);\n"
                f"        return 0;\n"
                f"    }}"
            )
        set_fn = f"""int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value)
{{
    if(!ui || !name) return -1;
{chr(10).join(cases)}
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
    else:
        set_fn = """int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value)
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

    header = f"""#ifndef QVGL_PREVIEW_SHIM_H
#define QVGL_PREVIEW_SHIM_H

#include "lvgl.h"
#include <stdint.h>

#include "ui_{name}.h"

typedef {ui_type} qvgl_preview_ui_t;

void qvgl_preview_ui_create(lv_obj_t * parent, qvgl_preview_ui_t * ui);
void qvgl_preview_ui_sync(qvgl_preview_ui_t * ui);
int qvgl_preview_set_property(qvgl_preview_ui_t * ui, const char * name, float value);
uint32_t qvgl_preview_property_count(void);
const char * qvgl_preview_property_name(uint32_t index);
int32_t qvgl_preview_width(void);
int32_t qvgl_preview_height(void);
const char * qvgl_preview_title(void);

#endif
"""

    source = f"""#include "qvgl_preview_shim.h"
{extra_include}
#include <string.h>

void qvgl_preview_ui_create(lv_obj_t * parent, qvgl_preview_ui_t * ui)
{{
    qvgl_ui_{name}_create(parent, ui);
}}

{sync_fn}
{set_fn}
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
"""

    (out_dir / "qvgl_preview_shim.h").write_text(header, encoding="utf-8")
    (out_dir / "qvgl_preview_shim.c").write_text(source, encoding="utf-8")
