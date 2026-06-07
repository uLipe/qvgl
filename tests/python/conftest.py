from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def lvgl_path() -> Path:
    return LVGL


@pytest.fixture(scope="session")
def caps(lvgl_path: Path):
    if not lvgl_path.is_dir():
        pytest.skip("lvgl tree not found")
    from qvglc.lvgl_probe import probe_lvgl

    return probe_lvgl(lvgl_path)


def emit_qml_module(
    qml: Path,
    profile,
    out_dir: Path,
    caps,
    *,
    module_name: str | None = None,
) -> Path:
    from qvglc.emit_lvgl import emit_module
    from qvglc.parser import compile_qml

    name = module_name or qml.stem
    mod = compile_qml(qml, profile, name)
    asset_root = qml.parent if any(n.kind == "Image" for n in mod.nodes) else None
    emit_module(mod, caps, out_dir, asset_root=asset_root)
    return out_dir


@pytest.fixture
def emit_qml(caps):
    def _emit(qml: Path, profile, out_dir: Path, module_name: str | None = None) -> Path:
        return emit_qml_module(qml, profile, out_dir, caps, module_name=module_name)

    return _emit
