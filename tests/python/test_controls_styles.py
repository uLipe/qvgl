from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "examples/controls_styles/controls_styles.qml"


def test_controls_styles_parses():
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_styles")
    names = {p.name for p in mod.module_properties}
    assert names >= {"panelEnabled", "panelOpacity"}


def test_controls_styles_emit_markers(caps, tmp_path: Path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_styles")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_controls_styles.c").read_text(encoding="utf-8")
    for marker in (
        "LV_STATE_DISABLED",
        "LV_PART_INDICATOR",
        "qvgl_controls_set_enabled",
        "qvgl_widget_set_opa_f32",
        "app_on_enable_pressed",
        "app_on_enable_released",
        "LV_EVENT_PRESSED",
    ):
        assert marker in ui_c
