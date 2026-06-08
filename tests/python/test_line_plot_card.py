from __future__ import annotations

from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
QML = ROOT / "examples/line_plot_card/line_plot_card.qml"
FRAME = ROOT / "examples/line_plot_card/golden/frames/line_plot_card.png"

PLOT_MARKERS = [
    "qvgl_plot_t",
    "lv_chart_create",
    "LV_CHART_TYPE_SCATTER",
    "qvgl_plot_set_points",
    "qvgl_plot_set_domain",
    "qvgl_plot_apply_series",
    "qvgl_ui_line_plot_card_set_plot_points",
    "qvgl_ui_line_plot_card_apply_plot_series",
]

HOVER_MARKERS = [
    "qvgl_plot_set_crosshair",
    "qvgl_plot_clear_crosshair",
    "set_plot_cursor",
    "_hover_cb",
    "qvgl_line_plot_card_set_cursorText",
    "_cross_v",
]


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    from qvglc.lvgl_probe import probe_lvgl

    return probe_lvgl(LVGL)


@pytest.fixture
def profile():
    return load_profile(PROFILE)


def test_line_plot_card_parses(profile):
    mod = compile_qml(QML, profile, "line_plot_card")
    plot = next(n for n in mod.nodes if n.kind == "LinePlot")
    assert len(plot.properties.get("series", [])) == 11


def test_line_plot_hover_emit_markers(profile, caps, tmp_path: Path):
    mod = compile_qml(QML, profile, "line_plot_card")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_line_plot_card.c").read_text(encoding="utf-8")
    for marker in HOVER_MARKERS:
        assert marker in ui_c, marker


def test_line_plot_emit_markers(profile, caps, tmp_path: Path):
    mod = compile_qml(QML, profile, "line_plot_card")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_line_plot_card.c").read_text(encoding="utf-8")
    for marker in PLOT_MARKERS:
        assert marker in ui_c, marker


def test_line_plot_card_render_golden(profile, caps, tmp_path: Path):
    if not FRAME.is_file():
        pytest.skip("render golden not committed")
    gen = tmp_path / "gen"
    mod = compile_qml(QML, profile, "line_plot_card")
    emit_module(mod, caps, gen, asset_root=QML.parent)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out)
    assert_qvgl_golden_match(out, FRAME, per_channel_tolerance=18)
