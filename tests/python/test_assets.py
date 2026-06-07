from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qvglc.emit_lvgl import EmitError, emit_module
from qvglc.emit_lvgl.assets import _png_to_argb8888
from qvglc.emit_lvgl.widget_style import image_layout
from qvglc.layout import Rect
from qvglc.parser import compile_qml
from qvglc.profile import load_profile
from qvglc.lvgl_probe import probe_lvgl
from png_compare import assert_qvgl_golden_match
from qvgl_snapshot import build_preview, dump_preview_frame

ROOT = Path(__file__).resolve().parents[2]
LVGL = ROOT.parent / "lvgl"
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
CLUSTER_PROFILE = ROOT / "profiles/cluster_480x272.yaml"

ICON_QML = ROOT / "examples/icon_row/icon_row.qml"
ICON_FRAME = ROOT / "examples/icon_row/golden/frames/icon_row.png"

INSTRUMENT_QML = ROOT / "examples/instrument_cluster_static/instrument_cluster_static.qml"

STATIC_CARD_QML = ROOT / "examples/static_card/static_card.qml"
THEMED_CHIP_QML = ROOT / "examples/themed_chip/themed_chip.qml"


def _make_dot_png(path: Path, rgb: tuple[int, int, int]) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (16, 16), (*rgb, 255))
    px = img.load()
    for y in range(16):
        for x in range(16):
            if (x - 7) ** 2 + (y - 7) ** 2 > 49:
                px[x, y] = (0, 0, 0, 0)
    img.save(path)


@pytest.fixture(scope="module", autouse=True)
def icon_assets():
    assets = ICON_QML.parent / "assets"
    _make_dot_png(assets / "dot_red.png", (220, 40, 40))
    _make_dot_png(assets / "dot_green.png", (40, 200, 80))
    _make_dot_png(assets / "dot_amber.png", (240, 180, 40))


@pytest.fixture
def profile():
    return load_profile(PROFILE)


@pytest.fixture
def cluster_profile():
    return load_profile(CLUSTER_PROFILE)


@pytest.fixture
def caps():
    if not LVGL.is_dir():
        pytest.skip("lvgl tree not found")
    return probe_lvgl(LVGL)


def test_png_to_argb8888_byte_order(icon_assets, tmp_path):
    from PIL import Image

    p = tmp_path / "px.png"
    Image.new("RGBA", (1, 1), (0x11, 0x22, 0x33, 0x44)).save(p)
    w, h, blob = _png_to_argb8888(p)
    assert (w, h) == (1, 1)
    assert blob == bytes([0x33, 0x22, 0x11, 0x44])


def test_profile_font_tiers(cluster_profile):
    assert cluster_profile.font_for_pixel_size(10) == "montserrat_14"
    assert cluster_profile.font_for_pixel_size(22) == "montserrat_36"
    assert cluster_profile.font_for_pixel_size(90) == "montserrat_48"


def test_profile_theme_tokens(cluster_profile):
    assert cluster_profile.theme_colors["cluster_bg"] == "#00414a"


def test_theme_resolves_in_ir(cluster_profile):
    mod = compile_qml(THEMED_CHIP_QML, cluster_profile, "themed_chip")
    root = mod.nodes[mod.root]
    assert root.properties["color"] == "#ff00414a"
    chip = mod.nodes[root.children[0]]
    assert chip.properties["color"] == "#ff2cde85"
    assert chip.properties["border.color"] == "#ff28c878"


def test_image_layout_preserve_aspect_fit():
    box = image_layout(Rect(0, 0, 32, 32), 16, 16, "PreserveAspectFit")
    assert box == Rect(0, 0, 32, 32)
    box2 = image_layout(Rect(10, 10, 40, 20), 16, 16, "PreserveAspectFit")
    assert box2.w == 20
    assert box2.h == 20
    assert box2.x == 20
    assert box2.y == 10


def test_border_emit_markers(profile, caps, tmp_path):
    mod = compile_qml(STATIC_CARD_QML, profile, "static_card")
    emit_module(mod, caps, tmp_path, asset_root=STATIC_CARD_QML.parent)
    ui_c = (tmp_path / "ui_static_card.c").read_text(encoding="utf-8")
    assert "lv_obj_set_style_border_width" in ui_c
    assert "lv_obj_set_style_border_color" in ui_c


def test_fillmode_emit_preserve_aspect(profile, caps, tmp_path):
    mod = compile_qml(ICON_QML, profile, "icon_row")
    emit_module(mod, caps, tmp_path, asset_root=ICON_QML.parent)
    ui_c = (tmp_path / "ui_icon_row.c").read_text(encoding="utf-8")
    assert "lv_obj_set_size(ui->image_1, 32, 32)" in ui_c


def test_image_emit_requires_asset_root(profile, caps, tmp_path):
    mod = compile_qml(ICON_QML, profile, "icon_row")
    with pytest.raises(EmitError, match="asset_root"):
        emit_module(mod, caps, tmp_path)


def test_image_emit_markers(profile, caps, tmp_path):
    mod = compile_qml(ICON_QML, profile, "icon_row")
    emit_module(mod, caps, tmp_path, asset_root=ICON_QML.parent)
    ui_c = (tmp_path / "ui_icon_row.c").read_text(encoding="utf-8")
    assets_c = (tmp_path / "qvgl_icon_row_assets.c").read_text(encoding="utf-8")
    conf = (tmp_path / "qvgl_lv_conf.h").read_text(encoding="utf-8")
    assert "lv_image_create" in ui_c
    assert "lv_image_set_src(ui->" in ui_c
    assert "qvgl_asset_dot_red" in assets_c
    assert "LV_USE_IMAGE" in conf
    assert "LV_FONT_MONTSERRAT_14" in conf


def test_opacity_emit_hidden(cluster_profile, caps, tmp_path):
    mod = compile_qml(INSTRUMENT_QML, cluster_profile, "instrument_cluster_static")
    emit_module(mod, caps, tmp_path, asset_root=INSTRUMENT_QML.parent)
    ui_c = (tmp_path / "ui_instrument_cluster_static.c").read_text(encoding="utf-8")
    assert ui_c.count("LV_OBJ_FLAG_HIDDEN") >= 2
    assert "lv_font_montserrat_48" in ui_c


def test_icon_row_render_golden(profile, caps, tmp_path):
    if not ICON_FRAME.is_file():
        pytest.skip("render golden not committed")
    gen = tmp_path / "gen"
    mod = compile_qml(ICON_QML, profile, "icon_row")
    emit_module(mod, caps, gen, asset_root=ICON_QML.parent)
    preview = build_preview(tmp_path / "b", gen.resolve(), LVGL)
    out = tmp_path / "frame.png"
    dump_preview_frame(preview, gen.resolve(), out)
    assert_qvgl_golden_match(out, ICON_FRAME)
