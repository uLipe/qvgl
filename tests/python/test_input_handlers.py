from __future__ import annotations

from pathlib import Path

from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profiles/ultralite_v1.yaml"

INPUT_QML = """import QtQuick 2.15

Item {
    width: 100
    height: 100

    MouseArea {
        id: tapArea
        anchors.fill: parent
        onPressed: app_on_area_pressed()
        onReleased: app_on_area_released()
    }
}
"""


def test_mouse_area_pressed_released_emit(caps, tmp_path: Path):
    qml = tmp_path / "input_handlers.qml"
    qml.write_text(INPUT_QML, encoding="utf-8")
    prof = load_profile(PROFILE)
    mod = compile_qml(qml, prof, "input_handlers")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_input_handlers.c").read_text(encoding="utf-8")
    assert "qvgl_input_handlers_tap_area_pressed_cb" in ui_c
    assert "qvgl_input_handlers_tap_area_released_cb" in ui_c
    assert "LV_EVENT_PRESSED" in ui_c
    assert "LV_EVENT_RELEASED" in ui_c
