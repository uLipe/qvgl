from __future__ import annotations

from qvglc.emit_lvgl.colors import lv_color_hex_expr
from qvglc.ir.model import Node
from qvglc.layout import Rect
from qvglc.profile import Profile


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


def emit_opacity_visible(node: Node, var: str) -> list[str]:
    lines: list[str] = []
    if "visible" in node.properties and not node.properties.get("visible", True):
        lines.append(f"    lv_obj_add_flag({var}, LV_OBJ_FLAG_HIDDEN);")
    if "opacity" in node.properties:
        opa = float(node.properties["opacity"])
        if opa <= 0.0:
            lines.append(f"    lv_obj_add_flag({var}, LV_OBJ_FLAG_HIDDEN);")
        elif opa < 1.0:
            lv_opa = max(0, min(255, int(round(opa * 255))))
            lines.append(f"    lv_obj_set_style_opa({var}, {lv_opa}, 0);")
    return lines


def emit_enabled(node: Node, var: str) -> list[str]:
    if "enabled" in node.properties and not node.properties.get("enabled", True):
        return [f"    lv_obj_clear_flag({var}, LV_OBJ_FLAG_CLICKABLE);"]
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
