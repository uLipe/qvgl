from __future__ import annotations

import shutil
from pathlib import Path

from .emit_apply import emit_vehicle_apply, load_bindings


def maybe_emit_vehicle_bind(qml_or_dir: Path, out_dir: Path) -> list[Path]:
    base = qml_or_dir.parent if qml_or_dir.suffix == ".qml" else qml_or_dir
    bindings_path = base / "vehicle_bindings.yaml"
    if not bindings_path.is_file():
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bindings_path, out_dir / bindings_path.name)
    return emit_vehicle_apply(load_bindings(bindings_path), out_dir)
