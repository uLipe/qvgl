from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
MANIFEST = ROOT / "examples/conformance/manifest.yaml"


def _pass_cases() -> list[dict]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return [c for c in data["cases"] if c["tier"] == "pass"]


def _run_cmd(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    return subprocess.run(
        ["qvglc", "run", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )


@pytest.fixture
def build_dir(tmp_path):
    return tmp_path / "build"


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_qvglc_run_cli_loop_frames(build_dir: Path):
    r = _run_cmd(
        [
            "examples/mcu_minimal/minimal.qml",
            "--build-dir",
            str(build_dir),
            "--lvgl-path",
            str(LVGL),
            "--headless",
            "--exit",
            "--loop-frames",
            "5",
        ],
        build_dir,
    )
    assert r.returncode == 0, r.stderr or r.stdout


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
@pytest.mark.parametrize("case", _pass_cases(), ids=lambda c: c["id"])
def test_qvglc_run_cli_pass_examples(case: dict, build_dir: Path):
    qml = ROOT / case["qml"]
    profile = ROOT / case["profile"]
    extra: list[str] = []
    if case["id"] == "cluster_dual_gauge":
        extra = ["--set", "speed_kmh=80", "--set", "rpm=2500"]
    r = _run_cmd(
        [
            str(qml.relative_to(ROOT)),
            "--build-dir",
            str(build_dir / case["id"]),
            "--lvgl-path",
            str(LVGL),
            "--profile",
            str(profile.relative_to(ROOT)),
            "--headless",
            "--exit",
            "--loop-frames",
            "3",
            *extra,
        ],
        build_dir,
    )
    assert r.returncode == 0, f"{case['id']}: {r.stderr or r.stdout}"
