from __future__ import annotations

from pathlib import Path

import pytest

from qvglc.emit_lvgl.conf import emit_qvgl_sdkconfig_defaults, merge_sdkconfig_fragment
from qvglc.parser import compile_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profiles/ultralite_v1.yaml"
MATERIAL_QML = ROOT / "examples/material_card/material_card.qml"


def test_material_card_sdkconfig_includes_montserrat_36():
    prof = load_profile(PROFILE)
    mod = compile_qml(MATERIAL_QML, prof, "material_card")
    from qvglc.emit_lvgl.conf import collect_required_fonts

    fonts = collect_required_fonts(mod, prof)
    assert "montserrat_36" in fonts
    text = emit_qvgl_sdkconfig_defaults(fonts=fonts, use_image=False)
    assert "CONFIG_LV_FONT_MONTSERRAT_36=y" in text
    assert "CONFIG_LV_USE_SLIDER=y" in text


def test_merge_sdkconfig_enables_disabled_font(tmp_path: Path):
    fragment = tmp_path / "qvgl_sdkconfig.defaults"
    sdkconfig = tmp_path / "sdkconfig"
    fragment.write_text(
        "# generated\nCONFIG_LV_FONT_MONTSERRAT_36=y\nCONFIG_LV_USE_SLIDER=y\n",
        encoding="utf-8",
    )
    sdkconfig.write_text(
        "CONFIG_LV_FONT_MONTSERRAT_14=y\n# CONFIG_LV_FONT_MONTSERRAT_36 is not set\n",
        encoding="utf-8",
    )
    assert merge_sdkconfig_fragment(fragment, sdkconfig) is True
    merged = sdkconfig.read_text(encoding="utf-8")
    assert "CONFIG_LV_FONT_MONTSERRAT_36=y" in merged
    assert "# CONFIG_LV_FONT_MONTSERRAT_36 is not set" not in merged
    assert "CONFIG_LV_USE_SLIDER=y" in merged
    assert merge_sdkconfig_fragment(fragment, sdkconfig) is False
