from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
QML = ROOT / "examples/channel_plot_trim/channel_plot_trim.qml"


def test_channel_plot_trim_responsive_emit(caps, tmp_path: Path):
    mod = compile_qml(QML, load_profile(PROFILE), "channel_plot_trim")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_channel_plot_trim.c").read_text(encoding="utf-8")
    assert "LV_PCT(100)" in ui_c
    assert "LV_LAYOUT_FLEX" in ui_c
    assert "lv_obj_set_flex_grow(ui->lineplot_" in ui_c
    assert "qvgl_plot_relayout" in ui_c
    assert "x_unit_label" in ui_c
    assert "axis_bottom" in ui_c
    assert "_resize_cb" in ui_c
    assert 'lv_snprintf(ui->cursorText' in ui_c or 'cursorText[64]' in (tmp_path / "ui_channel_plot_trim.h").read_text(encoding="utf-8")
