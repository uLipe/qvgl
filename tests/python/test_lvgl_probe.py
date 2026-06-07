from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.lvgl_probe import probe_lvgl
from qvglc.lvgl_probe.probe import LvglProbeError

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"


def test_probe_real_lvgl():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    caps = probe_lvgl(LVGL)
    assert caps.major >= 9
    assert caps.features["LV_USE_ARC"] == 1
    assert caps.features["LV_USE_LABEL"] == 1


def test_probe_missing_dir(tmp_path: Path):
    with pytest.raises(LvglProbeError):
        probe_lvgl(tmp_path / "nope")


def test_require_arc():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    caps = probe_lvgl(LVGL)
    caps.require_arc_gauge()
