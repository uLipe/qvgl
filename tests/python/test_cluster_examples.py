from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.ir import load_json_path, module_to_dict
from qvglc.layout import Rect, resolve_layout
from qvglc.lvgl_probe import probe_lvgl
from qvglc.parser import compile_qml
from qvglc.profile import load_profile
from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
CLUSTER_PROFILE = ROOT / "profiles/cluster_480x272.yaml"

CLUSTER_QML = ROOT / "examples/cluster_shell/cluster_shell.qml"
CLUSTER_GOLDEN = ROOT / "examples/cluster_shell/golden/cluster_shell.qvglir.json"
CLUSTER_FRAME = ROOT / "examples/cluster_shell/golden/frames/cluster_shell.png"

INSTRUMENT_QML = ROOT / "examples/instrument_cluster_static/instrument_cluster_static.qml"
INSTRUMENT_GOLDEN = ROOT / "examples/instrument_cluster_static/golden/instrument_cluster_static.qvglir.json"
INSTRUMENT_FRAME = ROOT / "examples/instrument_cluster_static/golden/frames/instrument_cluster_static.png"

CLUSTER_LAYOUT = {
    0: Rect(0, 0, 480, 272),
    1: Rect(0, 0, 480, 40),
    3: Rect(24, 56, 120, 120),
    4: Rect(336, 56, 120, 120),
    5: Rect(0, 240, 480, 32),
}

EMIT_MARKERS = {
    "cluster_shell": [
        'lv_label_set_text(ui->text_2, "CLUSTER")',
        "lv_color_hex(0x1a1a2e)",
        "lv_obj_set_style_radius(ui->gauge_left, 8, 0)",
    ],
    "instrument_cluster_static": [
        'lv_label_set_text(ui->speedometer, "0")',
        "lv_color_hex(0x00414a)",
        'lv_label_set_text(ui->text_2, "km/h")',
        "lv_font_montserrat_48",
        "LV_OBJ_FLAG_HIDDEN",
    ],
}


def _norm(d: dict) -> dict:
    return json.loads(json.dumps(d, sort_keys=True))


@pytest.fixture
def cluster_profile():
    return load_profile(CLUSTER_PROFILE)


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


@pytest.mark.parametrize(
    "qml,name,golden",
    [
        (CLUSTER_QML, "cluster_shell", CLUSTER_GOLDEN),
        (INSTRUMENT_QML, "instrument_cluster_static", INSTRUMENT_GOLDEN),
    ],
)
def test_qml_ir_golden(qml, name, golden, cluster_profile):
    mod = compile_qml(qml, cluster_profile, name)
    expected = load_json_path(golden)
    assert _norm(module_to_dict(mod)) == _norm(module_to_dict(expected))


def test_cluster_shell_layout(cluster_profile):
    mod = compile_qml(CLUSTER_QML, cluster_profile, "cluster_shell")
    lay = resolve_layout(mod)
    assert lay[mod.root].rect == Rect(0, 0, 480, 272)
    for idx, rect in CLUSTER_LAYOUT.items():
        assert lay[idx].rect == rect
    assert lay[2].align_center is True
    assert lay[6].align_center is True


def test_instrument_cluster_static_layout(cluster_profile):
    mod = compile_qml(
        INSTRUMENT_QML, cluster_profile, "instrument_cluster_static"
    )
    lay = resolve_layout(mod)
    assert lay[mod.root].rect == Rect(0, 0, 480, 272)
    assert lay[1].align_center is True
    assert lay[1].align_center_offset_y == 0
    assert lay[2].align_center_offset_y < -60
    assert lay[3].align_center_offset_y > 100
    assert lay[4].align_center_offset_y > 80
    assert lay[2].align_center_offset_y < lay[1].align_center_offset_y
    assert lay[4].align_center_offset_y < lay[3].align_center_offset_y
    assert lay[4].align_center_offset_y > lay[1].align_center_offset_y


@pytest.mark.parametrize("name,markers", [
    ("cluster_shell", EMIT_MARKERS["cluster_shell"]),
    ("instrument_cluster_static", EMIT_MARKERS["instrument_cluster_static"]),
])
def test_emit_markers(name, markers, cluster_profile, caps, tmp_path):
    qml = CLUSTER_QML if name == "cluster_shell" else INSTRUMENT_QML
    mod = compile_qml(qml, cluster_profile, name)
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / f"ui_{name}.c").read_text(encoding="utf-8")
    for m in markers:
        assert m in ui_c


def test_cluster_shell_render_golden(caps, cluster_profile, emit_qml, tmp_path):
    if not CLUSTER_FRAME.is_file():
        pytest.skip("render golden not committed")
    gen = tmp_path / "gen"
    emit_qml(CLUSTER_QML, cluster_profile, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out)
    assert_qvgl_golden_match(out, CLUSTER_FRAME)


def test_instrument_cluster_static_render_golden(caps, cluster_profile, emit_qml, tmp_path):
    if not INSTRUMENT_FRAME.is_file():
        pytest.skip("render golden not committed")
    gen = tmp_path / "gen"
    emit_qml(INSTRUMENT_QML, cluster_profile, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out)
    assert_qvgl_golden_match(out, INSTRUMENT_FRAME)

