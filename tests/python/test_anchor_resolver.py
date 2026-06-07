from __future__ import annotations

import json
from pathlib import Path

import pytest

from qvglc.ir import load_json_path, module_to_dict
from qvglc.layout import Rect, resolve_layout
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
TURBO_QML = ROOT / "examples/turbo_gauge/turbo_gauge.qml"
TURBO_GOLDEN = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir.json"
MINIMAL_QML = ROOT / "examples/mcu_minimal/minimal.qml"
MINIMAL_GOLDEN = ROOT / "examples/mcu_minimal/golden/minimal.qvglir.json"


def _norm_float(x: float) -> float:
    return float(f"{x:.6g}")


def _normalize_obj(obj):
    if isinstance(obj, float):
        return _norm_float(obj)
    if isinstance(obj, dict):
        return {k: _normalize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_obj(v) for v in obj]
    return obj


def _normalize(d: dict) -> dict:
    return json.loads(json.dumps(_normalize_obj(d), sort_keys=True))


def _rect(layouts, idx) -> Rect:
    return layouts[idx].rect


@pytest.fixture
def profile():
    return load_profile(default_profile_path())


def test_turbo_qml_ir_includes_anchors(profile):
    mod = compile_qml(TURBO_QML, profile, "turbo_gauge")
    golden = load_json_path(TURBO_GOLDEN)
    assert _normalize(module_to_dict(mod)) == _normalize(module_to_dict(golden))


def test_minimal_qml_ir_includes_anchors(profile):
    mod = compile_qml(MINIMAL_QML, profile, "minimal")
    golden = load_json_path(MINIMAL_GOLDEN)
    assert _normalize(module_to_dict(mod)) == _normalize(module_to_dict(golden))


def test_turbo_gauge_anchor_layout(profile):
    mod = compile_qml(TURBO_QML, profile, "turbo_gauge")
    lay = resolve_layout(mod)

    assert _rect(lay, 0) == Rect(0, 0, 400, 400)
    assert _rect(lay, 1) == Rect(0, 0, 400, 400)
    assert _rect(lay, 2) == Rect(40, 40, 320, 320)
    assert _rect(lay, 5) == Rect(0, 0, 400, 400)

    assert lay[3].align_center is True
    title = _rect(lay, 4)
    assert title.center_x == 200
    assert title.y < lay[3].rect.center_y


def test_minimal_anchor_layout(profile):
    mod = compile_qml(MINIMAL_QML, profile, "minimal")
    lay = resolve_layout(mod)

    assert _rect(lay, 0) == Rect(0, 0, 400, 400)
    assert lay[1].align_center is True


def test_static_card_anchor_layout(profile):
    qml = ROOT / "examples/static_card/static_card.qml"
    mod = compile_qml(qml, profile, "static_card")
    lay = resolve_layout(mod)

    assert _rect(lay, 0) == Rect(0, 0, 320, 240)
    assert _rect(lay, 1) == Rect(0, 0, 320, 240)
    assert lay[2].align_center is True


def test_edge_anchors_stretch_panel(profile):
    qml = ROOT / "tests/fixtures/qml/layout/edge_anchors.qml"
    mod = compile_qml(qml, profile, "edge_anchors")
    lay = resolve_layout(mod)

    assert _rect(lay, 0) == Rect(0, 0, 400, 400)
    assert _rect(lay, 1) == Rect(20, 16, 120, 40)
    body = _rect(lay, 2)
    assert body == Rect(20, 68, 360, 312)


def test_fill_with_uniform_margins(profile):
    qml = """
import QtQuick 2.15
Item {
    width: 200
    height: 100
    Rectangle {
        anchors.fill: parent
        anchors.margins: 10
    }
}
"""
    mod = compile_qml(qml, profile, "margins")
    lay = resolve_layout(mod)
    assert _rect(lay, 1) == Rect(10, 10, 180, 80)
