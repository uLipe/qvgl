from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
TURBO = ROOT / "examples/turbo_gauge/turbo_gauge.qml"
GAUGE_TICKS = ROOT / "examples/gauge_ticks/gauge_ticks.qml"


def test_turbo_gauge_responsive_emit(caps, tmp_path: Path):
    mod = compile_qml(TURBO, load_profile(PROFILE), "turbo_gauge")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_turbo_gauge.c").read_text(encoding="utf-8")
    assert "LV_PCT(100)" in ui_c
    assert "LV_ALIGN_CENTER" in ui_c
    assert "lv_obj_align(ui->gauge_arc" in ui_c


def test_gauge_ticks_responsive_emit(caps, tmp_path: Path):
    mod = compile_qml(GAUGE_TICKS, load_profile(PROFILE), "gauge_ticks")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_gauge_ticks.c").read_text(encoding="utf-8")
    assert "LV_PCT(100)" in ui_c
    assert "lv_obj_align(ui->gauge_arc_scale" in ui_c
