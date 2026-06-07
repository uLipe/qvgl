from __future__ import annotations

import re


_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def parse_color_hex(s: str) -> int:
    if not isinstance(s, str) or not _HEX_RE.match(s):
        raise ValueError(f"invalid color: {s!r}")
    h = s[1:]
    if len(h) == 8:
        h = h[2:]
    return int(h, 16)


def lv_color_hex_expr(s: str) -> str:
    return f"lv_color_hex(0x{parse_color_hex(s):06x})"
