from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.emit_lvgl.emitter import emit_module
from qvglc.emit_lvgl.layout import layout_module
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
CONTROLS_QML = ROOT / "examples/controls_card/controls_card.qml"


@pytest.fixture(scope="module")
def profile():
    return load_profile(default_profile_path())


@pytest.fixture(scope="module")
def controls_mod(profile):
    return compile_qml(CONTROLS_QML, profile, "controls_card")


def test_controls_card_parses(profile):
    compile_qml(CONTROLS_QML, profile, "controls_card")


def test_controls_card_has_layout_nodes(controls_mod):
    kinds = {n.kind for n in controls_mod.nodes}
    assert "ColumnLayout" in kinds
    assert "RowLayout" in kinds
    assert "Text" in kinds
    assert "ToolButton" in kinds


def test_controls_card_flex_layout(controls_mod):
    layouts = layout_module(controls_mod)
    by_id = {n.id: i for i, n in enumerate(controls_mod.nodes) if n.id}
    plot_area_idx = next(
        i
        for i, n in enumerate(controls_mod.nodes)
        if n.kind == "Rectangle" and n.properties.get("color") == "#ff0d0d0f"
    )
    lay = layouts[plot_area_idx]
    assert lay.rect.w >= 200
    assert lay.rect.h >= 80


def test_controls_card_emits_toolbutton(controls_mod, tmp_path, caps):
    emit_module(controls_mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_controls_card.c").read_text(encoding="utf-8")
    assert "lv_button_create" in ui_c
    assert "app_on_plot_close" in ui_c


def test_channel_plot_card_rejects_function(profile):
    qml = (ROOT.parent / "ChannelPlotCard.qml").read_text(encoding="utf-8")
    from qvglc.parser import QvglDiagnostic, check_qml

    with pytest.raises(QvglDiagnostic) as exc:
        check_qml(qml, profile)
    assert exc.value.code.value in (
        "unsupported_feature",
        "unsupported_expr",
        "parse_syntax",
        "unknown_import",
        "unknown_type",
    )
