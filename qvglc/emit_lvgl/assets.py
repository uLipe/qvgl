from __future__ import annotations

import re
from pathlib import Path

from qvglc.ir.model import Module, Node

from .emit_context import EmitContext
from .errors import EmitError


def _asset_id(source: str) -> str:
    base = Path(source).stem
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", base)
    if not safe or safe[0].isdigit():
        safe = f"img_{safe}"
    return safe.lower()


def collect_image_nodes(mod: Module) -> list[tuple[Node, str]]:
    out: list[tuple[Node, str]] = []
    for node in mod.nodes:
        if node.kind != "Image":
            continue
        src = node.properties.get("source")
        if not isinstance(src, str) or not src:
            raise EmitError(f"Image node {node.id!r} requires string source")
        out.append((node, src))
    return out


def _png_to_argb8888(path: Path) -> tuple[int, int, bytes]:
    try:
        from PIL import Image
    except ImportError as e:
        raise EmitError("Pillow required for Image emit (pip install pillow)") from e

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()
    data = bytearray()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            data.extend((b, g, r, a))
    return w, h, bytes(data)


def emit_assets(
    mod: Module,
    ctx: EmitContext,
    out_dir: Path,
) -> tuple[Path, dict[str, tuple[str, int, int]]]:
    images = collect_image_nodes(mod)
    if not images:
        return out_dir / f"qvgl_{mod.module}_assets.h", {}

    sources = sorted({src for _, src in images})
    id_by_source: dict[str, tuple[str, int, int]] = {}

    maps: list[str] = []
    dscs: list[str] = []
    for src in sources:
        aid = _asset_id(src)
        path = ctx.resolve_asset(src)
        w, h, blob = _png_to_argb8888(path)
        id_by_source[src] = (aid, w, h)
        stride = w * 4
        hex_lines = []
        row: list[str] = []
        for i, byte in enumerate(blob):
            row.append(f"0x{byte:02x}")
            if len(row) == 16:
                hex_lines.append("    " + ",".join(row) + ",")
                row = []
        if row:
            hex_lines.append("    " + ",".join(row) + ",")
        maps.append(
            f"static const uint8_t qvgl_asset_{aid}_map[] = {{\n"
            + "\n".join(hex_lines)
            + "\n};"
        )
        dscs.append(
            f"const lv_image_dsc_t qvgl_asset_{aid} = {{\n"
            f"    .header = {{\n"
            f"        .magic = LV_IMAGE_HEADER_MAGIC,\n"
            f"        .cf = LV_COLOR_FORMAT_ARGB8888,\n"
            f"        .flags = 0,\n"
            f"        .w = {w},\n"
            f"        .h = {h},\n"
            f"        .stride = {stride},\n"
            f"        .reserved_2 = 0,\n"
            f"    }},\n"
            f"    .data_size = sizeof(qvgl_asset_{aid}_map),\n"
            f"    .data = qvgl_asset_{aid}_map,\n"
            f"    .reserved = NULL,\n"
            f"}};"
        )

    header = f"""#ifndef QVGL_{mod.module.upper()}_ASSETS_H
#define QVGL_{mod.module.upper()}_ASSETS_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {{
#endif

{chr(10).join(f"extern const lv_image_dsc_t qvgl_asset_{id_by_source[s][0]};" for s in sources)}

#ifdef __cplusplus
}}
#endif

#endif
"""

    source = f"""#include "qvgl_{mod.module}_assets.h"

{chr(10).join(maps)}

{chr(10).join(dscs)}
"""

    out_dir.mkdir(parents=True, exist_ok=True)
    header_path = out_dir / f"qvgl_{mod.module}_assets.h"
    source_path = out_dir / f"qvgl_{mod.module}_assets.c"
    header_path.write_text(header, encoding="utf-8")
    source_path.write_text(source, encoding="utf-8")
    return header_path, id_by_source
