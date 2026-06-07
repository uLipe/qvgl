from __future__ import annotations

from pathlib import Path

from qvglc.ir.model import Module
from qvglc.lvgl_probe.probe import LvglCapabilities

from .emit_context import EmitContext
from .errors import EmitError
from .hybrid_ui import emit_hybrid
from .static_ui import emit_static

_SUPPORTED_PROFILES = frozenset({"ultralite_v1", "cluster_480x272"})


def emit_module(
    mod: Module,
    caps: LvglCapabilities,
    out_dir: Path,
    *,
    asset_root: Path | None = None,
) -> list[Path]:
    if mod.profile not in _SUPPORTED_PROFILES:
        raise EmitError(f"unsupported profile: {mod.profile}")
    ctx = EmitContext(asset_root=asset_root)
    if any(n.kind == "Arc" for n in mod.nodes):
        return emit_hybrid(mod, caps, out_dir, ctx)
    return emit_static(mod, caps, out_dir, ctx)
