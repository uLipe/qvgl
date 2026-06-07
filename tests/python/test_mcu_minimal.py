from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from qvglc.emit_lvgl import emit_module
from qvglc.ir import encode_module, load_json_path, module_to_dict, validate
from qvglc.lvgl_probe import probe_lvgl
from qvglc.parser import check_qml, compile_qml, default_profile_path, load_profile, parse_qml
from qvglc.parser.sema import analyze
from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.run_preview import run_qml_preview

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
FIXTURE = ROOT / "examples/mcu_minimal/minimal.qml"
UPSTREAM_SHA = ROOT / "examples/mcu_minimal/UPSTREAM.sha256"
GOLDEN_JSON = ROOT / "examples/mcu_minimal/golden/minimal.qvglir.json"
GOLDEN_FRAME = ROOT / "examples/mcu_minimal/golden/frames/minimal.png"
SYNCED = ROOT / "examples/upstream/synced/mcu_minimal/minimal.qml"

# Qt for MCUs "minimal" example — Ultralite-compatible getting started screen.
MCU_MINIMAL_SPEC = {
    "import": "QtQuick 2.15",
    "root_kind": "Rectangle",
    "root_color": "#41CD52",
    "text": "Qt for MCUs",
    "font_pixel_size": 30,
    "anchor": "centerIn",
}

EMIT_MARKERS = [
    'lv_label_set_text(ui->text_1, "Qt for MCUs")',
    "lv_color_hex(0x41cd52)",
    "lv_obj_align(ui->text_1, LV_ALIGN_CENTER",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


@pytest.fixture
def profile():
    return load_profile(default_profile_path())


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


def test_fixture_upstream_sha256_pinned():
    assert FIXTURE.is_file()
    assert UPSTREAM_SHA.is_file()
    assert _sha256(FIXTURE) == UPSTREAM_SHA.read_text(encoding="utf-8").strip()


def test_qt_quick_import_and_sema(profile):
    src = FIXTURE.read_text(encoding="utf-8")
    assert f"import {MCU_MINIMAL_SPEC['import']}" in src
    check_qml(FIXTURE, profile)


def test_ast_matches_ultralite_minimal_shape(profile):
    doc = parse_qml(FIXTURE.read_text(encoding="utf-8"))
    analyze(doc, profile)
    assert doc.root is not None
    assert doc.root.type_name == MCU_MINIMAL_SPEC["root_kind"]
    assert len(doc.root.children) == 1

    color = next(v for n, v, _ in doc.root.properties if n == "color")
    assert color == MCU_MINIMAL_SPEC["root_color"]

    text_obj = doc.root.children[0]
    assert text_obj.type_name == "Text"
    props = {n: v for n, v, _ in text_obj.properties}
    assert props["text"] == MCU_MINIMAL_SPEC["text"]
    assert props["font.pixelSize"] == MCU_MINIMAL_SPEC["font_pixel_size"]
    assert props["anchors.centerIn"] == {"op": "sym", "name": "parent"}


def test_qml_ir_matches_golden(profile):
    mod = compile_qml(FIXTURE, profile, module_name="minimal")
    validate(mod)
    golden = load_json_path(GOLDEN_JSON)
    assert _normalize(module_to_dict(mod)) == _normalize(module_to_dict(golden))


def test_ir_json_binary_roundtrip(profile):
    mod = compile_qml(FIXTURE, profile, module_name="minimal")
    blob = encode_module(mod)
    from qvglc.ir import decode_binary

    back = decode_binary(blob)
    validate(back)
    assert _normalize(module_to_dict(back)) == _normalize(module_to_dict(mod))


def test_emit_minimal_markers(profile, caps, tmp_path: Path):
    mod = compile_qml(FIXTURE, profile, module_name="minimal")
    emit_module(mod, caps, tmp_path)
    ui_c = (tmp_path / "ui_minimal.c").read_text(encoding="utf-8")
    for marker in EMIT_MARKERS:
        assert marker in ui_c, marker


def test_render_golden_frame(caps, profile, tmp_path: Path):
    if not GOLDEN_FRAME.is_file():
        pytest.skip("render golden PNG not committed")

    from conftest import emit_qml_module

    gen = tmp_path / "gen"
    emit_qml_module(FIXTURE, profile, gen, caps)
    preview = build_preview(tmp_path / "build", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out, cwd=ROOT)
    assert_qvgl_golden_match(out, GOLDEN_FRAME)


def test_qvglc_run_headless_smoke(tmp_path: Path):
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    rc = run_qml_preview(
        FIXTURE,
        build_dir=tmp_path / "build",
        lvgl_path=LVGL,
        headless=True,
        loop_frames=30,
        exit_after=True,
    )
    assert rc == 0


def test_synced_upstream_sdk_same_ir_as_fixture(profile):
    if not SYNCED.is_file():
        pytest.skip("run tools/sync_upstream_examples.sh to compare against Qt SDK")
    mod_fixture = compile_qml(FIXTURE, profile, module_name="minimal")
    mod_synced = compile_qml(SYNCED, profile, module_name="minimal")
    assert _normalize(module_to_dict(mod_fixture)) == _normalize(module_to_dict(mod_synced))


def test_qvglc_compile_cli(tmp_path: Path):
    out = tmp_path / "gen"
    proc = subprocess.run(
        ["qvglc", "compile", str(FIXTURE), "-o", str(out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert (out / "ui_minimal.c").is_file()
    assert (out / "qvgl_preview_shim.c").is_file()
