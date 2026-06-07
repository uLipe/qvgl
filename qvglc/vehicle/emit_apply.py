from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class VehicleBindError(Exception):
    pass


def _snake_id(name: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and (name[i - 1].islower() or (i + 1 < len(name) and name[i + 1].islower())):
            out.append("_")
        out.append(ch.lower())
    return "".join(out).replace("-", "_")


def load_bindings(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VehicleBindError(f"invalid bindings file: {path}")
    module = data.get("module")
    mappings = data.get("mappings")
    lamps = data.get("warning_lamps")
    if not module or not isinstance(mappings, list):
        raise VehicleBindError("bindings require module and mappings list")
    if not mappings and not lamps:
        raise VehicleBindError("bindings need non-empty mappings and/or warning_lamps")
    for row in mappings:
        if not isinstance(row, dict) or "vehicle" not in row or "property" not in row:
            raise VehicleBindError("each mapping needs vehicle and property keys")
    if lamps is not None:
        if not isinstance(lamps, list):
            raise VehicleBindError("warning_lamps must be a list")
        for row in lamps:
            if not isinstance(row, dict) or "bit" not in row or "image" not in row:
                raise VehicleBindError("each warning_lamps row needs bit and image keys")
    return data


def emit_vehicle_apply(bindings: dict[str, Any], out_dir: Path) -> list[Path]:
    module = str(bindings["module"])
    mod_upper = module.upper()
    mappings: list[dict[str, str]] = bindings["mappings"]

    apply_decls: list[str] = []
    for row in mappings:
        vehicle = row["vehicle"]
        prop = row["property"]
        fn = f"qvgl_{module}_set_{prop}"
        apply_decls.append(f"    {fn}(ui, st->{vehicle});")

    for row in bindings.get("warning_lamps") or []:
        bit = str(row["bit"])
        field = _snake_id(str(row["image"]))
        apply_decls.append(
            f"    if(st->warnings & {bit}) lv_obj_clear_flag(ui->{field}, LV_OBJ_FLAG_HIDDEN);\n"
            f"    else lv_obj_add_flag(ui->{field}, LV_OBJ_FLAG_HIDDEN);"
        )

    pub_include = f'#include "qvgl_{module}.h"\n' if mappings else ""
    header = f"""#ifndef QVGL_{mod_upper}_VEHICLE_H
#define QVGL_{mod_upper}_VEHICLE_H

#include "qvgl/qvgl_vehicle_model.h"
#include "ui_{module}.h"
{pub_include}

#ifdef __cplusplus
extern "C" {{
#endif

static inline void qvgl_{module}_apply_vehicle(
    qvgl_ui_{module}_t * ui,
    const qvgl_vehicle_state_t * st)
{{
    if(!ui || !st) return;
{chr(10).join(apply_decls)}
}}

#ifdef __cplusplus
}}
#endif

#endif
"""

    out_dir.mkdir(parents=True, exist_ok=True)
    h_path = out_dir / f"qvgl_{module}_vehicle.h"
    h_path.write_text(header, encoding="utf-8")
    paths = [h_path]

    preview_c = f"""#include "qvgl_preview_vehicle.h"
#include "qvgl_{module}_vehicle.h"
#include "qvgl/qvgl_vehicle_model.h"
#include "qvgl_preview_shim.h"

#include <stdlib.h>
#include <string.h>

static int parse_can_hex(const char * arg, uint32_t * can_id, uint8_t * data, uint8_t * dlc)
{{
    const char * colon = strchr(arg, ':');
    if(!colon || colon == arg) return -1;
    char id_buf[16];
    size_t id_len = (size_t)(colon - arg);
    if(id_len >= sizeof(id_buf)) return -1;
    memcpy(id_buf, arg, id_len);
    id_buf[id_len] = '\\0';
    *can_id = (uint32_t)strtoul(id_buf, NULL, 0);
    const char * hex = colon + 1;
    if(!hex[0]) return -1;
    size_t hex_len = strlen(hex);
    if(hex_len % 2 != 0 || hex_len / 2 > 8) return -1;
    *dlc = (uint8_t)(hex_len / 2);
    for(uint8_t i = 0; i < *dlc; i++) {{
        char pair[3] = {{ hex[i * 2], hex[i * 2 + 1], '\\0' }};
        data[i] = (uint8_t)strtoul(pair, NULL, 16);
    }}
    return 0;
}}

void qvgl_preview_vehicle_apply_can(qvgl_preview_ui_t * ui, const char * can_arg)
{{
    if(!ui || !can_arg) return;
    uint32_t can_id = 0;
    uint8_t data[8];
    uint8_t dlc = 0;
    if(parse_can_hex(can_arg, &can_id, data, &dlc) != 0) return;
    qvgl_vehicle_state_t st;
    qvgl_vehicle_state_init(&st);
    if(qvgl_vehicle_decode_demo_can(can_id, data, dlc, &st))
        qvgl_{module}_apply_vehicle(ui, &st);
}}
"""
    preview_h = """#ifndef QVGL_PREVIEW_VEHICLE_H
#define QVGL_PREVIEW_VEHICLE_H

#include "qvgl_preview_shim.h"

void qvgl_preview_vehicle_apply_can(qvgl_preview_ui_t * ui, const char * can_arg);

#endif
"""
    (out_dir / "qvgl_preview_vehicle.c").write_text(preview_c, encoding="utf-8")
    (out_dir / "qvgl_preview_vehicle.h").write_text(preview_h, encoding="utf-8")
    paths.extend([out_dir / "qvgl_preview_vehicle.c", out_dir / "qvgl_preview_vehicle.h"])
    return paths
