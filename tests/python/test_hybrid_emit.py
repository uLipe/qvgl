from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.emit_lvgl.bindings_codegen import property_consumers
from qvglc.ir import load_json_path
from qvglc.lvgl_probe import probe_lvgl
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
TURBO_GOLDEN = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir.json"
BOUND_QML = ROOT / "examples/bound_label/bound_label.qml"


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


def test_property_consumers_turbo():
    mod = load_json_path(TURBO_GOLDEN)
    consumers = property_consumers(mod)
    assert "pressure" in consumers
    assert len(consumers["pressure"]) == 2


def test_turbo_hybrid_emit_markers(caps, tmp_path):
    mod = load_json_path(TURBO_GOLDEN)
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_turbo_gauge.c").read_text(encoding="utf-8")
    shim_h = (tmp_path / "qvgl_preview_shim.h").read_text(encoding="utf-8")
    for marker in (
        "qvgl_turbo_gauge_set_pressure",
        "lv_arc_create",
        "qvgl_widget_set_arc_value",
        "int qvgl_preview_set_property",
        "qvgl_preview_apply_property",
    ):
        assert marker in ui_c or marker in shim_h


def test_bound_label_setters(caps, tmp_path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(BOUND_QML, prof, "bound_label")
    consumers = property_consumers(mod)
    assert "value" in consumers
    assert len(consumers["value"]) >= 1

    emit_module(mod, caps, tmp_path)
    pub_h = (tmp_path / "qvgl_bound_label.h").read_text(encoding="utf-8")
    assert "qvgl_bound_label_set_value" in pub_h


def test_static_module_no_setters(caps, tmp_path):
    prof = load_profile(default_profile_path())
    qml = ROOT / "examples/mcu_minimal/minimal.qml"
    mod = compile_qml(qml, prof, "minimal")
    emit_module(mod, caps, tmp_path)
    assert not (tmp_path / "qvgl_minimal.h").exists()
    shim = (tmp_path / "qvgl_preview_shim.h").read_text(encoding="utf-8")
    assert "qvgl_preview_property_count" in shim
