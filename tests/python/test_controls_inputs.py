from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "examples/controls_inputs/controls_inputs.qml"


def test_controls_inputs_parses():
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_inputs")
    kinds = {n.kind for n in mod.nodes}
    assert "Slider" in kinds
    assert "Switch" in kinds
    assert "CheckBox" in kinds
    assert "Button" in kinds
    assert "ComboBox" in kinds
    assert mod.module_properties
    names = {p.name for p in mod.module_properties}
    assert names >= {"gain", "outputEnabled", "mute", "preset"}
    preset_box = next(n for n in mod.nodes if n.id == "presetBox")
    assert preset_box.properties.get("model") == ["Off", "Low", "High"]


def test_controls_inputs_emit_markers(caps, tmp_path: Path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_inputs")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_controls_inputs.c").read_text(encoding="utf-8")
    pub_h = (tmp_path / "qvgl_controls_inputs.h").read_text(encoding="utf-8")
    for marker in (
        "lv_slider_create",
        "lv_switch_create",
        "lv_checkbox_create",
        "lv_dropdown_create",
        "lv_button_create",
        "qvgl_controls_inputs_set_gain",
        "qvgl_controls_inputs_set_preset",
        "qvgl_widget_set_slider_value",
        "qvgl_widget_set_checked",
        "qvgl_widget_set_dropdown_selected",
        "app_on_gain_moved",
        "app_on_gain_changed",
        "app_on_preset_activated",
        "app_on_apply_clicked",
        "LV_EVENT_VALUE_CHANGED",
        "Off\\nLow\\nHigh",
    ):
        assert marker in ui_c or marker in pub_h
