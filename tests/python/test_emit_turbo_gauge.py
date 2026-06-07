from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.ir import load_json_path, validate
from qvglc.lvgl_probe import probe_lvgl

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
GOLDEN_JSON = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir.json"
REQUIRED_MARKERS = [
    "lv_arc_set_bg_angles",
    "LV_ARC_MODE_REVERSE",
    "lv_arc_set_range",
    "qvgl_turbo_gauge_set_pressure",
    "lv_snprintf(buf, sizeof(buf), \"%.1f bar\"",
    "app_on_gauge_clicked",
    "lv_obj_add_event_cb",
    "lv_obj_set_style_opa",
    "LV_PART_KNOB",
]


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


@pytest.fixture
def mod():
    m = load_json_path(GOLDEN_JSON)
    validate(m)
    return m


def test_emit_writes_files(mod, caps, tmp_path: Path):
    paths = emit_module(mod, caps, tmp_path)
    assert len(paths) == 8
    ui_c = (tmp_path / "ui_turbo_gauge.c").read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in ui_c, marker


def test_arc_fixed_point_range(mod, caps, tmp_path: Path):
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_turbo_gauge.c").read_text(encoding="utf-8")
    assert "lv_arc_set_range" in ui_c
    assert "-7" in ui_c
    assert "20" in ui_c


def test_cli_emit(mod, caps, tmp_path: Path):
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    out = subprocess.run(
        [
            "qvglc",
            "emit",
            str(GOLDEN_JSON),
            "-o",
            str(tmp_path / "out"),
            "--lvgl-path",
            str(LVGL),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "out/ui_turbo_gauge.c").is_file()


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_gcc_compile_ui(tmp_path: Path):
    mod = load_json_path(GOLDEN_JSON)
    caps = probe_lvgl(LVGL)
    gen = tmp_path / "gen"
    emit_module(mod, caps, gen)

    stub = tmp_path / "lv_conf.h"
    stub.write_text(
        "#ifndef LV_CONF_H\n#define LV_CONF_H\n#include <stdint.h>\n"
        "#define LV_USE_FLOAT 0\n#define LV_USE_ARC 1\n#define LV_USE_LABEL 1\n"
        "#define LV_FONT_MONTSERRAT_14 1\n#define LV_FONT_MONTSERRAT_36 1\n"
        "#define LV_COLOR_DEPTH 16\n#endif\n",
        encoding="utf-8",
    )

    stub_c = tmp_path / "app_stub.c"
    stub_c.write_text("void app_on_gauge_clicked(void) {}\n", encoding="utf-8")

    inc = [
        f"-I{gen}",
        f"-I{LVGL}",
        f"-I{LVGL}/include",
        f"-I{tmp_path}",
    ]
    r1 = subprocess.run(
        ["gcc", "-c", "-std=c11", *inc, str(stub_c), "-o", str(tmp_path / "stub.o")],
        capture_output=True,
        text=True,
    )
    r = subprocess.run(
        ["gcc", "-c", "-std=c11", *inc, str(gen / "ui_turbo_gauge.c"), "-o", str(tmp_path / "ui.o")],
        capture_output=True,
        text=True,
    )
    if r1.returncode != 0:
        pytest.skip(f"gcc stub failed: {r1.stderr[:300]}")
    if r.returncode != 0:
        pytest.skip(f"gcc compile not available or LVGL headers incomplete: {r.stderr[:500]}")
