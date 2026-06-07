from __future__ import annotations

from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.vehicle import emit_vehicle_apply, load_bindings, maybe_emit_vehicle_bind

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
QML = ROOT / "examples/warning_telltales/warning_telltales.qml"
BINDINGS = ROOT / "examples/warning_telltales/vehicle_bindings.yaml"
PROFILE = ROOT / "profiles/cluster_480x272.yaml"
FRAME = ROOT / "examples/warning_telltales/golden/frames/warning_telltales_oil_abs.png"

# speed=0 rpm=0 gear=0 warnings=0x05 (oil + abs)
CAN_WARN = "0x200:000000000005"


def test_warning_bindings_load():
    data = load_bindings(BINDINGS)
    assert data["module"] == "warning_telltales"
    assert len(data["warning_lamps"]) == 3


def test_warning_lamps_emit_apply(tmp_path: Path):
    data = load_bindings(BINDINGS)
    paths = emit_vehicle_apply(data, tmp_path)
    text = paths[0].read_text(encoding="utf-8")
    assert "ui->oil_lamp" in text
    assert "QVGL_WARN_OIL_PRESSURE" in text
    assert "lv_obj_clear_flag" in text
    assert (tmp_path / "qvgl_preview_vehicle.c").is_file()


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_warning_telltales_can_render(caps, emit_qml, tmp_path: Path):
    if not FRAME.is_file():
        pytest.skip("render golden not committed")

    from qvglc.profile import load_profile

    prof = load_profile(PROFILE)
    gen = tmp_path / "gen"
    emit_qml(QML, prof, gen)
    maybe_emit_vehicle_bind(QML, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(
        preview,
        gen.resolve(),
        out,
        can_frames=[CAN_WARN],
        frames=5,
        cwd=ROOT,
    )
    assert_qvgl_golden_match(out, FRAME)
