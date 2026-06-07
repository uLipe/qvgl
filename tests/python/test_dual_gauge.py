from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from qvglc.ir import load_json_path, module_to_dict
from qvglc.lvgl_probe import probe_lvgl
from qvglc.parser import compile_qml
from qvglc.profile import load_profile
from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.run_preview import run_qml_preview

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
PROFILE = ROOT / "profiles/cluster_480x272.yaml"
QML = ROOT / "examples/cluster_dual_gauge/cluster_dual_gauge.qml"
GOLDEN = ROOT / "examples/cluster_dual_gauge/golden/cluster_dual_gauge.qvglir.json"
FRAMES = ROOT / "examples/cluster_dual_gauge/golden/frames"


def _norm(d: dict) -> dict:
    return json.loads(json.dumps(d, sort_keys=True))


@pytest.fixture
def cluster_profile():
    return load_profile(PROFILE)


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


def test_qml_ir_golden(cluster_profile):
    mod = compile_qml(QML, cluster_profile, "cluster_dual_gauge")
    expected = load_json_path(GOLDEN)
    assert _norm(module_to_dict(mod)) == _norm(module_to_dict(expected))


@pytest.mark.parametrize(
    "sets,name",
    [
        ([], "cluster_dual_gauge_default.png"),
        (["speed_kmh=130", "rpm=4000"], "cluster_dual_gauge_mid.png"),
    ],
)
def test_render_golden(caps, cluster_profile, emit_qml, tmp_path, sets, name):
    golden = FRAMES / name
    if not golden.is_file():
        pytest.skip(f"golden not committed: {golden}")
    gen = tmp_path / "gen"
    emit_qml(QML, cluster_profile, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out, prop_sets=sets)
    assert_qvgl_golden_match(out, golden)


def test_run_with_generic_set(tmp_path):
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    rc = run_qml_preview(
        QML,
        build_dir=tmp_path / "build",
        lvgl_path=LVGL,
        profile_path=PROFILE,
        headless=True,
        prop_sets=["speed_kmh=80", "rpm=2500"],
        loop_frames=15,
        exit_after=True,
    )
    assert rc == 0
