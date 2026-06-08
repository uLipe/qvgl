from __future__ import annotations

from pathlib import Path

import pytest

from conformance_util import emit_tier_cases, load_emit_markers
from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def markers_by_id() -> dict[str, list[str]]:
    return load_emit_markers()


@pytest.mark.parametrize("case", emit_tier_cases(), ids=lambda c: c["id"])
def test_conformance_emit_markers(case: dict, caps, markers_by_id: dict[str, list[str]], tmp_path: Path):
    case_id = case["id"]
    required = markers_by_id.get(case_id)
    if not required:
        pytest.skip(f"no emit markers for {case_id}")

    qml = ROOT / case["qml"]
    profile = load_profile(ROOT / case["profile"])
    mod = compile_qml(qml, profile, case_id)
    asset_root = qml.parent if any(n.kind == "Image" for n in mod.nodes) else None
    emit_module(mod, caps, tmp_path, asset_root=asset_root)

    ui_c = (tmp_path / f"ui_{case_id}.c").read_text(encoding="utf-8")
    pub_h = tmp_path / f"qvgl_{case_id}.h"
    extra = pub_h.read_text(encoding="utf-8") if pub_h.is_file() else ""
    blob = ui_c + extra
    for marker in required:
        assert marker in blob, f"{case_id}: missing emit marker {marker!r}"
