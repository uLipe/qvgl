from __future__ import annotations

from pathlib import Path

import pytest

from png_compare import assert_qvgl_vs_qt_match
from qt_parity_render import (
    ROOT,
    load_qt_parity_cases,
    render_qt_snapshot,
    render_qvgl_snapshot,
    viewport_size,
)

LVGL = ROOT.parent / "lvgl"

pytest.importorskip("PyQt6.QtQuick")

CASES = load_qt_parity_cases()


@pytest.fixture(scope="session")
def lvgl_path():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return LVGL.resolve()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_qt_qvgl_render_parity(case: dict, tmp_path: Path, lvgl_path: Path):
    qml = ROOT / case["qml"]
    profile = ROOT / case["profile"]
    assert qml.is_file(), qml

    w, h = viewport_size(qml, profile)

    work = tmp_path / case["id"]
    qt_png = work / "qt.png"
    qvgl_png = work / "qvgl.png"

    render_qt_snapshot(qml, w, h, qt_png)
    render_qvgl_snapshot(
        qml,
        profile,
        qvgl_png,
        build_dir=work / "build",
        lvgl_path=lvgl_path,
        prop_sets=case.get("set"),
    )

    assert_qvgl_vs_qt_match(
        qvgl_png,
        qt_png,
        per_channel_tolerance=int(case.get("per_channel_tolerance", 12)),
        max_diff_ratio=float(case.get("max_diff_ratio", 0.05)),
    )
