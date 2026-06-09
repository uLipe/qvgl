from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import apply_mcu_root_display, compile_qml, load_profile
from qvglc.profile import apply_display_override

ROOT = Path(__file__).resolve().parents[2]
P4_PROFILE = ROOT / "profiles/esp32p4_1024x600.yaml"
QML = ROOT / "examples/channel_plot_trim/channel_plot_trim.qml"


def test_esp32p4_profile_display():
    prof = load_profile(P4_PROFILE)
    assert prof.display_width == 1024
    assert prof.display_height == 600
    assert prof.type_names() >= {"LinePlot", "Slider"}


def test_display_override():
    prof = load_profile(ROOT / "profiles/ultralite_v1.yaml")
    apply_display_override(prof, 800, 480)
    assert prof.display_width == 800
    assert prof.display_height == 480


def test_mcu_root_emit_uses_profile_size(caps, tmp_path: Path):
    prof = load_profile(P4_PROFILE)
    mod = compile_qml(QML, prof, "channel_plot_trim")
    apply_mcu_root_display(mod, prof)
    emit_module(mod, caps, tmp_path)
    shim = (tmp_path / "qvgl_preview_shim.c").read_text(encoding="utf-8")
    assert "return 1024;" in shim
    assert "return 600;" in shim
    ui_c = (tmp_path / "ui_channel_plot_trim.c").read_text(encoding="utf-8")
    assert "LV_PCT(100)" in ui_c
    assert "qvgl_plot_relayout" in ui_c
