from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
QML = ROOT / "examples/channel_plot_trim/channel_plot_trim.qml"


def test_channel_plot_trim_parses():
    prof = load_profile(PROFILE)
    mod = compile_qml(QML, prof, "channel_plot_trim")
    names = {p.name for p in mod.module_properties}
    assert names >= {"plotTitle", "unit", "cursorText"}


def test_channel_plot_trim_emit_bindings(caps, tmp_path: Path):
    prof = load_profile(PROFILE)
    mod = compile_qml(QML, prof, "channel_plot_trim")
    emit_module(mod, caps, tmp_path)
    pub = (tmp_path / "qvgl_channel_plot_trim.h").read_text(encoding="utf-8")
    ui_c = (tmp_path / "ui_channel_plot_trim.c").read_text(encoding="utf-8")
    assert "qvgl_channel_plot_trim_set_cursorText" in pub
    assert "qvgl_channel_plot_trim_set_plotTitle" in pub
    assert "apply_plot_series" in ui_c
    assert "qvgl_widget_set_visible(ui->cursor_label" in ui_c
