from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.vehicle import (
    apply_can_arg,
    emit_vehicle_apply,
    load_bindings,
    prop_sets_from_can_args,
    vehicle_state_init,
)
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


def test_demo_can_decode_matches_c_layout():
    st = vehicle_state_init()
    assert apply_can_arg(st, "0x200:B004AC0D0300")
    assert abs(st.speed_kmh - 120.0) < 0.01
    assert abs(st.rpm - 3500.0) < 0.01
    assert st.gear == 3


def test_prop_sets_from_can_args():
    sets = prop_sets_from_can_args(["0x200:1405A00F"], BINDINGS)
    assert "speed_kmh=130" in sets
    assert "rpm=4000" in sets


def test_compile_emits_vehicle_bind(caps, tmp_path: Path):
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    out = subprocess.run(
        [
            "python3",
            "-m",
            "qvglc.cli",
            "compile",
            str(QML),
            "-o",
            str(tmp_path / "gen"),
            "--profile",
            str(PROFILE),
            "--lvgl-path",
            str(LVGL),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert out.returncode == 0, out.stderr
    gen = tmp_path / "gen"
    assert (gen / "qvgl_cluster_dual_gauge_vehicle.h").is_file()
    assert (gen / "vehicle_bindings.yaml").is_file()


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_run_with_can_frame(tmp_path: Path):
    r = subprocess.run(
        [
            "python3",
            "-m",
            "qvglc.cli",
            "run",
            str(QML),
            "--build-dir",
            str(tmp_path / "build"),
            "--lvgl-path",
            str(LVGL),
            "--profile",
            str(PROFILE),
            "--can",
            "0x200:1405A00F",
            "--headless",
            "--exit",
            "--loop-frames",
            "5",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**__import__("os").environ, "SDL_VIDEODRIVER": "dummy"},
    )
    assert r.returncode == 0, r.stderr or r.stdout


def test_can_frame_drives_render_golden(caps, emit_qml, tmp_path: Path):
    if not FRAME_MID.is_file():
        pytest.skip("render golden not committed")

    sets = prop_sets_from_can_args(["0x200:1405A00F"], BINDINGS)
    from qvglc.profile import load_profile

    prof = load_profile(PROFILE)
    gen = tmp_path / "gen"
    emit_qml(QML, prof, gen)
    from qvglc.vehicle import maybe_emit_vehicle_bind

    maybe_emit_vehicle_bind(QML, gen)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out, prop_sets=sets, cwd=ROOT)
    assert_qvgl_golden_match(out, FRAME_MID)


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
