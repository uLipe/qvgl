from __future__ import annotations

from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.ir.model import Node
from qvglc.layout import Rect
from qvglc.profile import Profile
from qvglc.theme import resolve_theme_member


def lv_font_expr(profile: Profile, pixel_size: int) -> str:
    font_id = profile.font_for_pixel_size(pixel_size)
    return f"&lv_font_{font_id}"


def image_layout(box: Rect, img_w: int, img_h: int, fill_mode: str) -> Rect:
    if fill_mode == "Stretch" or img_w <= 0 or img_h <= 0:
        return box
    if fill_mode == "PreserveAspectFit":
        scale = min(box.w / img_w, box.h / img_h)
        fw = max(1, int(img_w * scale))
        fh = max(1, int(img_h * scale))
        return Rect(box.x + (box.w - fw) // 2, box.y + (box.h - fh) // 2, fw, fh)
    return box


def _is_bound(val: object) -> bool:
    return isinstance(val, dict) and "binding" in val


def emit_opacity_visible(node: Node, var: str) -> list[str]:
    lines: list[str] = []
    vis = node.properties.get("visible")
    if "visible" in node.properties and not _is_bound(vis) and not vis:
        lines.append(f"    lv_obj_add_flag({var}, LV_OBJ_FLAG_HIDDEN);")
    opa_val = node.properties.get("opacity")
    if "opacity" in node.properties and not _is_bound(opa_val):
        opa = float(opa_val)
        if opa <= 0.0:
            lines.append(f"    lv_obj_add_flag({var}, LV_OBJ_FLAG_HIDDEN);")
        elif opa < 1.0:
            lv_opa = max(0, min(255, int(round(opa * 255))))
            lines.append(f"    lv_obj_set_style_opa({var}, {lv_opa}, 0);")
    return lines


def emit_enabled(node: Node, var: str) -> list[str]:
    en = node.properties.get("enabled")
    if "enabled" in node.properties and not _is_bound(en) and not en:
        return [f"    lv_obj_add_state({var}, LV_STATE_DISABLED);"]
    return []


def emit_material_control_chrome(node: Node, var: str, profile: Profile) -> list[str]:
    accent = lv_color_hex_expr(resolve_theme_member(profile, "accent"))
    track = lv_color_hex_expr(resolve_theme_member(profile, "secondary"))
    if node.kind == "Slider":
        return [
            f"    lv_obj_set_style_bg_color({var}, {track}, LV_PART_MAIN);",
            f"    lv_obj_set_style_bg_color({var}, {accent}, LV_PART_INDICATOR);",
            f"    lv_obj_set_style_radius({var}, 4, LV_PART_MAIN);",
            f"    lv_obj_set_style_radius({var}, 4, LV_PART_INDICATOR);",
            f"    lv_obj_set_style_pad_all({var}, 4, LV_PART_MAIN);",
        ]
    if node.kind == "Switch":
        return [
            f"    lv_obj_set_style_bg_color({var}, {track}, LV_PART_MAIN);",
            f"    lv_obj_set_style_bg_color({var}, {accent}, LV_PART_INDICATOR);",
        ]
    if node.kind == "ComboBox":
        return [
            f"    lv_obj_set_style_border_width({var}, 1, 0);",
            f"    lv_obj_set_style_border_color({var}, {track}, 0);",
            f"    lv_obj_set_style_radius({var}, 4, 0);",
            f"    lv_obj_set_style_pad_hor({var}, 8, 0);",
        ]
    return []


def emit_border(node: Node, var: str) -> list[str]:
    bw = int(node.properties.get("border.width", 0))
    if bw <= 0:
        return []
    bc = node.properties.get("border.color", "#ffffffff")
    return [
        f"    lv_obj_set_style_border_width({var}, {bw}, 0);",
        f"    lv_obj_set_style_border_color({var}, {lv_color_hex_expr(str(bc))}, 0);",
        f"    lv_obj_set_style_border_opa({var}, LV_OPA_COVER, 0);",
    ]
