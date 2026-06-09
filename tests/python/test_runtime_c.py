from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"


@pytest.fixture(scope="module")
def cmake_build(tmp_path_factory) -> Path:
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    build = tmp_path_factory.mktemp("qvgl_cbuild")
    subprocess.run(
        [
            "cmake",
            "-B",
            str(build),
            "-S",
            str(ROOT),
            f"-DQVGL_LVGL_PATH={LVGL}",
            "-DQVGL_BUILD_PREVIEW=OFF",
        ],
        check=True,
        cwd=ROOT,
    )
    subprocess.run(["cmake", "--build", str(build), "-j"], check=True, cwd=ROOT)
    return build


def test_ctest_runtime_unit(cmake_build: Path):
    subprocess.run(
        ["ctest", "--test-dir", str(cmake_build), "-R", "^runtime_unit$", "--output-on-failure"],
        check=True,
        cwd=ROOT,
    )


def test_ctest_runtime_lvgl_widget(cmake_build: Path):
    subprocess.run(
        ["ctest", "--test-dir", str(cmake_build), "-R", "^runtime_lvgl_widget$", "--output-on-failure"],
        check=True,
        cwd=ROOT,
    )


def test_ctest_runtime_lvgl_controls(cmake_build: Path):
    subprocess.run(
        ["ctest", "--test-dir", str(cmake_build), "-R", "^runtime_lvgl_controls$", "--output-on-failure"],
        check=True,
        cwd=ROOT,
    )


def test_ctest_runtime_lvgl_plot(cmake_build: Path):
    subprocess.run(
        ["ctest", "--test-dir", str(cmake_build), "-R", "^runtime_lvgl_plot$", "--output-on-failure"],
        check=True,
        cwd=ROOT,
    )


def test_ctest_runtime_lvgl_bound(cmake_build: Path):
    subprocess.run(
        ["ctest", "--test-dir", str(cmake_build), "-R", "^runtime_lvgl_bound$", "--output-on-failure"],
        check=True,
        cwd=ROOT,
    )
