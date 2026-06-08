from __future__ import annotations

from pathlib import Path

import pytest

from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame
from qvglc.emit_lvgl import emit_module
from qvglc.parser import compile_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
QML = ROOT / "examples/warning_telltales/warning_telltales.qml"
FRAME = ROOT / "examples/warning_telltales/golden/frames/warning_telltales_oil_abs.png"


def test_warning_telltales_emit_markers(caps, tmp_path: Path):
    prof = load_profile(default_profile_path())
    mod = compile_qml(QML, prof, "warning_telltales")
    emit_module(mod, caps, tmp_path, asset_root=QML.parent)
    ui_c = (tmp_path / "ui_warning_telltales.c").read_text(encoding="utf-8")
    for marker in (
        "qvgl_warning_telltales_set_oilVisible",
        "qvgl_widget_set_visible(ui->oil_lamp",
        "lv_image_create",
    ):
        assert marker in ui_c


@pytest.mark.skipif(not LVGL.is_dir(), reason="lvgl tree not found")
def test_warning_telltales_render_golden(caps, tmp_path: Path):
    if not FRAME.is_file():
        pytest.skip("render golden not committed")

    prof = load_profile(default_profile_path())
    gen = tmp_path / "gen"
    mod = compile_qml(QML, prof, "warning_telltales")
    emit_module(mod, caps, gen, asset_root=QML.parent)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(
        preview,
        gen.resolve(),
        out,
        prop_sets=["oilVisible=true", "absVisible=true"],
        frames=5,
    )
    assert_qvgl_golden_match(out, FRAME)
