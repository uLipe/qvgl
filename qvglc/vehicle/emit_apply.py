from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class VehicleBindError(Exception):
    pass


def load_bindings(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VehicleBindError(f"invalid bindings file: {path}")
    module = data.get("module")
    mappings = data.get("mappings")
    if not module or not isinstance(mappings, list) or not mappings:
        raise VehicleBindError("bindings require module and non-empty mappings")
    for row in mappings:
        if not isinstance(row, dict) or "vehicle" not in row or "property" not in row:
            raise VehicleBindError("each mapping needs vehicle and property keys")
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

    header = f"""#ifndef QVGL_{mod_upper}_VEHICLE_H
#define QVGL_{mod_upper}_VEHICLE_H

#include "qvgl/qvgl_vehicle_model.h"
#include "ui_{module}.h"
#include "qvgl_{module}.h"

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
    return [h_path]
