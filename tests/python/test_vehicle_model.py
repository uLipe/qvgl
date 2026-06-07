from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.vehicle import emit_vehicle_apply, load_bindings
from qvglc.vehicle.emit_apply import VehicleBindError

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
BINDINGS = ROOT / "examples/cluster_dual_gauge/vehicle_bindings.yaml"
QML = ROOT / "examples/cluster_dual_gauge/cluster_dual_gauge.qml"
PROFILE = ROOT / "profiles/cluster_480x272.yaml"
FRAME_MID = ROOT / "examples/cluster_dual_gauge/golden/frames/cluster_dual_gauge_mid.png"


def test_vehicle_bindings_load():
    data = load_bindings(BINDINGS)
    assert data["module"] == "cluster_dual_gauge"
    assert len(data["mappings"]) == 2


def test_vehicle_bindings_reject_invalid(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("module: x\n", encoding="utf-8")
    with pytest.raises(VehicleBindError):
        load_bindings(bad)


def test_vehicle_bind_emit_markers(tmp_path: Path):
    data = load_bindings(BINDINGS)
    paths = emit_vehicle_apply(data, tmp_path)
    assert len(paths) == 1
    text = paths[0].read_text(encoding="utf-8")
    assert "qvgl_cluster_dual_gauge_apply_vehicle" in text
    assert "qvgl_cluster_dual_gauge_set_speed_kmh(ui, st->speed_kmh)" in text
    assert "qvgl_cluster_dual_gauge_set_rpm(ui, st->rpm)" in text


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_vehicle_cli_vehicle_bind(tmp_path: Path):
    out = subprocess.run(
        [
            "python3",
            "-m",
            "qvglc.cli",
            "vehicle-bind",
            str(BINDINGS),
            "-o",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "qvgl_cluster_dual_gauge_vehicle.h").is_file()


def test_vehicle_state_maps_to_setter_render(caps, emit_qml, tmp_path: Path):
    if not FRAME_MID.is_file():
        pytest.skip("render golden not committed")

    from qvglc.profile import load_profile

    prof = load_profile(PROFILE)
    gen = tmp_path / "gen"
    emit_qml(QML, prof, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(
        preview,
        gen.resolve(),
        out,
        prop_sets=["speed_kmh=130", "rpm=4000"],
        cwd=ROOT,
    )
    assert_qvgl_golden_match(out, FRAME_MID)
