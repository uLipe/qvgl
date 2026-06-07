from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.parser import QvglDiagnostic, check_qml, compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
ARC_QML = ROOT / "examples/arc_animated/arc_animated.qml"
CLUSTER_PROFILE = ROOT / "profiles/cluster_480x272.yaml"
REJECT = ROOT / "tests/fixtures/qml/reject/number_animation.qml"


def test_number_animation_on_opacity_rejected():
    prof = load_profile(CLUSTER_PROFILE)
    with pytest.raises(QvglDiagnostic) as exc:
        check_qml(REJECT, prof)
    assert exc.value.code.value == "unsupported_feature"


def test_arc_number_animation_parses():
    prof = load_profile(CLUSTER_PROFILE)
    check_qml(ARC_QML, prof)
    mod = compile_qml(ARC_QML, prof, "arc_animated")
    arc = next(n for n in mod.nodes if n.kind == "Arc")
    assert arc.properties.get("valueAnimationDuration") == 300
    assert not any(n.kind == "NumberAnimation" for n in mod.nodes)


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_arc_animation_emit_markers(caps, emit_qml, tmp_path: Path):
    prof = load_profile(CLUSTER_PROFILE)
    gen = tmp_path / "gen"
    emit_qml(ARC_QML, prof, gen)
    ui_c = (gen / "ui_arc_animated.c").read_text(encoding="utf-8")
    pub_h = (gen / "qvgl_arc_animated.h").read_text(encoding="utf-8")
    conf = (gen / "qvgl_lvgl.config").read_text(encoding="utf-8")
    assert "qvgl_arc_anim_exec_cb" in ui_c
    assert "lv_anim_set_duration" in ui_c
    assert "qvgl_arc_animated_set_level" in pub_h
    assert "config LV_USE_ANIM" in conf


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_arc_animation_setter_uses_lv_anim(caps, emit_qml, tmp_path: Path):
    prof = load_profile(CLUSTER_PROFILE)
    gen = tmp_path / "gen"
    emit_qml(ARC_QML, prof, gen)
    body = (gen / "ui_arc_animated.c").read_text(encoding="utf-8")
    assert "lv_anim_del" in body
    assert "lv_anim_start" in body
