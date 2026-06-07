from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame

from conftest import LVGL, ROOT, emit_qml_module

QML = ROOT / "examples/turbo_gauge/turbo_gauge.qml"
FRAMES = ROOT / "examples/turbo_gauge/golden/frames"
PREVIEW = ROOT / "build/tests/preview/qvgl_preview"

PRESSURE_CASES = [
    ("-0.7", -0.7),
    ("0.0", 0.0),
    ("2.0", 2.0),
]


def _preview_bin() -> Path:
    env = Path(__import__("os").environ.get("QVGL_PREVIEW_BIN", ""))
    if env.is_file():
        return env
    return PREVIEW


@pytest.fixture(scope="module")
def preview_bin(tmp_path_factory, caps):
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    from qvglc.parser import default_profile_path, load_profile

    gen = tmp_path_factory.mktemp("turbo_gen")
    prof = load_profile(default_profile_path())
    emit_qml_module(QML, prof, gen, caps)
    build_dir = tmp_path_factory.mktemp("preview_build")
    return build_preview(build_dir, gen.resolve(), LVGL), gen


@pytest.mark.parametrize("tag,pressure", PRESSURE_CASES)
def test_render_golden(preview_bin, tag: str, pressure: float, tmp_path: Path):
    preview, gen = preview_bin
    golden = FRAMES / f"turbo_gauge_p{tag}.png"
    if not golden.is_file():
        pytest.skip(f"golden missing: {golden}")

    out = tmp_path / f"frame_p{tag}.png"
    cmd = [
        str(preview),
        "--gen-dir",
        str(gen),
        "--headless",
        "--pressure",
        str(pressure),
        "--frames",
        "5",
        "--dump-fb",
        str(out),
    ]
    import os

    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
    assert r.returncode == 0, r.stderr
    assert_qvgl_golden_match(out, golden)


def test_preview_smoke_headless(preview_bin):
    preview, gen = preview_bin
    r = subprocess.run(
        [
            str(preview),
            "--gen-dir",
            str(gen),
            "--headless",
            "--loop-frames",
            "60",
            "--exit",
        ],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "SDL_VIDEODRIVER": "dummy"},
        cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
