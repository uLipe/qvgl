from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.emit_lvgl.bindings_codegen import property_consumers
from qvglc.parser import compile_qml, default_profile_path, load_profile
from qvglc.lvgl_probe import probe_lvgl

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
BOUND_QML = ROOT / "examples/bound_props_card/bound_props_card.qml"


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


def test_bound_props_consumers():
    prof = load_profile(default_profile_path())
    mod = compile_qml(BOUND_QML, prof, "bound_props_card")
    consumers = property_consumers(mod)
    assert set(consumers) == {"level", "channel", "alarm", "title"}
    assert len(consumers["title"]) == 1
    assert len(consumers["alarm"]) == 1
    assert consumers["alarm"][0][1] == "visible"


def test_bound_props_typed_emit(caps, tmp_path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(BOUND_QML, prof, "bound_props_card")
    emit_module(mod, caps, tmp_path)

    ui_h = (tmp_path / "ui_bound_props_card.h").read_text(encoding="utf-8")
    ui_c = (tmp_path / "ui_bound_props_card.c").read_text(encoding="utf-8")
    pub_h = (tmp_path / "qvgl_bound_props_card.h").read_text(encoding="utf-8")
    shim_h = (tmp_path / "qvgl_preview_shim.h").read_text(encoding="utf-8")

    for field in ("float level", "int32_t channel", "bool alarm", "char title[64]"):
        assert field in ui_h

    for decl in (
        "void qvgl_bound_props_card_set_level(qvgl_ui_bound_props_card_t * ui, float level)",
        "void qvgl_bound_props_card_set_channel(qvgl_ui_bound_props_card_t * ui, int32_t channel)",
        "void qvgl_bound_props_card_set_alarm(qvgl_ui_bound_props_card_t * ui, bool alarm)",
        "void qvgl_bound_props_card_set_title(qvgl_ui_bound_props_card_t * ui, const char * title)",
    ):
        assert decl in pub_h

    for marker in (
        "qvgl_widget_set_opa_f32(ui->alarm_bar",
        "qvgl_widget_set_visible(ui->alarm_bar",
        "qvgl_widget_set_text(ui->title_label",
        "qvgl_widget_set_text(ui->channel_label",
        'lv_snprintf(buf, sizeof(buf), "%d"',
    ):
        assert marker in ui_c

    assert "qvgl_preview_apply_property" in shim_h
