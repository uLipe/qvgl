from __future__ import annotations

from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml
from qvglc.profile import load_profile
from qvglc.lvgl_probe import probe_lvgl

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
QML = ROOT / "examples/gauge_ticks/gauge_ticks.qml"
FRAME = ROOT / "examples/gauge_ticks/golden/frames/gauge_ticks_p0.5.png"

SCALE_MARKERS = [
    "lv_scale_create",
    "LV_SCALE_MODE_ROUND_OUTER",
    "lv_scale_set_total_tick_count",
    "lv_scale_set_major_tick_every",
    "lv_scale_set_label_show",
    "gauge_arc_scale",
]


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


@pytest.fixture
def profile():
    return load_profile(PROFILE)


def test_arc_scale_emit_markers(profile, caps, tmp_path: Path):
    mod = compile_qml(QML, profile, "gauge_ticks")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_gauge_ticks.c").read_text(encoding="utf-8")
    for marker in SCALE_MARKERS:
        assert marker in ui_c, marker
    assert ui_c.index("lv_scale_create") < ui_c.index("lv_arc_create")


def test_gauge_ticks_render_golden(profile, caps, tmp_path: Path):
    if not FRAME.is_file():
        pytest.skip("render golden not committed")
    gen = tmp_path / "gen"
    mod = compile_qml(QML, profile, "gauge_ticks")
    emit_module(mod, caps, gen, asset_root=QML.parent)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out, prop_sets=["pressure=0.5"])
    assert_qvgl_golden_match(out, FRAME)
