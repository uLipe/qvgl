from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "examples/controls_p2/controls_p2.qml"


def test_controls_p2_parses():
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_p2")
    names = {p.name for p in mod.module_properties}
    assert names >= {"loadLevel", "ecoMode", "sportMode"}


def test_controls_p2_emit_markers(caps, tmp_path: Path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "controls_p2")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_controls_p2.c").read_text(encoding="utf-8")
    pub_h = (tmp_path / "qvgl_controls_p2.h").read_text(encoding="utf-8")
    for marker in (
        "lv_bar_create",
        "lv_obj_set_radio_button",
        "qvgl_controls_p2_set_loadLevel",
        "qvgl_controls_set_progress_value",
        "qvgl_controls_set_checked",
        "app_on_eco_selected",
        "app_on_sport_selected",
        "Drive mode",
    ):
        assert marker in ui_c or marker in pub_h
