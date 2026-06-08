from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.parser import QvglDiagnostic, check_qml, compile_qml, default_profile_path, load_profile
from qvglc.theme import merge_theme_aliases, resolve_theme_member

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "profiles/ultralite_v1.yaml"
THEMED_CHIP = ROOT / "examples/themed_chip/themed_chip.qml"
MATERIAL_CARD = ROOT / "examples/material_card/material_card.qml"
CONTROLS = ROOT / "examples/controls_card/controls_card.qml"
UNKNOWN_THEME = ROOT / "tests/fixtures/qml/reject/unknown_theme_token.qml"


@pytest.fixture
def profile():
    return load_profile(PROFILE_PATH)


def test_profile_material_aliases(profile):
    assert profile.theme_colors["background"] == profile.theme_colors["surface"]
    assert profile.theme_colors["primary"] == "#3d5a80"


def test_merge_theme_aliases():
    merged = merge_theme_aliases({"surface": "#111111"}, {"background": "surface"})
    assert merged["background"] == "#111111"


def test_resolve_theme_member(profile):
    assert resolve_theme_member(profile, "foreground") == "#ffe0e0e0"


def test_themed_chip_ir(profile):
    mod = compile_qml(THEMED_CHIP, profile, "themed_chip")
    root = mod.nodes[mod.root]
    assert root.properties["color"] == "#ff1a1a2e"


def test_material_card_ir(profile):
    mod = compile_qml(MATERIAL_CARD, profile, "material_card")
    root = mod.nodes[mod.root]
    assert root.properties["color"] == "#ff1a1a2e"
    accent_bar = mod.nodes[root.children[0]]
    assert accent_bar.properties["color"] == "#ff00d4aa"
    title = mod.nodes[root.children[1]]
    assert title.properties["color"] == "#ffe0e0e0"
    primary_label = mod.nodes[root.children[2]]
    assert primary_label.properties["color"] == "#ff3d5a80"


def test_controls_material_foreground_ir(profile):
    mod = compile_qml(CONTROLS, profile, "controls_card")
    labels = [n for n in mod.nodes if n.kind in ("Text", "Label")]
    assert any(n.properties.get("color") == "#ffe0e0e0" for n in labels)


def test_material_card_emit_bakes_colors(caps, tmp_path: Path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(MATERIAL_CARD, prof, "material_card")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_material_card.c").read_text(encoding="utf-8")
    assert "0x1a1a2e" in ui_c
    assert "0x00d4aa" in ui_c
    assert "0x3d5a80" in ui_c


def test_unknown_theme_token_rejected(profile):
    with pytest.raises(QvglDiagnostic) as exc:
        check_qml(UNKNOWN_THEME, profile)
    assert exc.value.code.value == "unsupported_expr"
    assert "notAToken" in str(exc.value)
