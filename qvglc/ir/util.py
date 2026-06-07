import struct


def fnv1a32(text: str) -> int:
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def bits_f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]


def parse_color(text: str) -> int:
    t = text.strip()
    if t.startswith("#"):
        t = t[1:]
    if len(t) == 6:
        return int(t, 16) | 0xFF000000
    if len(t) == 8:
        return int(t, 16)
    raise ValueError(f"invalid color: {text!r}")
