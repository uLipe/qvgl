from __future__ import annotations

from pathlib import Path


def swap_rb_channels(img):
    from PIL import Image

    out = img.convert("RGB").copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b = px[x, y]
            px[x, y] = (b, g, r)
    return out


def diff_pixel_count(
    actual: Path,
    expected: Path,
    *,
    per_channel_tolerance: int = 1,
    swap_rb_on_actual: bool = False,
    swap_rb_on_expected: bool = False,
) -> tuple[int, int]:
    from PIL import Image

    a = Image.open(actual)
    e = Image.open(expected)
    if swap_rb_on_actual:
        a = swap_rb_channels(a)
    else:
        a = a.convert("RGB")
    if swap_rb_on_expected:
        e = swap_rb_channels(e)
    else:
        e = e.convert("RGB")

    if a.size != e.size:
        raise AssertionError(f"size mismatch: {a.size} vs {e.size}")

    w, h = a.size
    apx, epx = a.load(), e.load()
    diff = 0
    for y in range(h):
        for x in range(w):
            ar, ag, ab = apx[x, y]
            er, eg, eb = epx[x, y]
            if (
                abs(ar - er) > per_channel_tolerance
                or abs(ag - eg) > per_channel_tolerance
                or abs(ab - eb) > per_channel_tolerance
            ):
                diff += 1
    return diff, w * h


def assert_qvgl_golden_match(
    actual: Path,
    expected: Path,
    *,
    per_channel_tolerance: int = 1,
) -> None:
    """Compare two QVGL preview PNGs (same BGR-in-PNG encoding, no channel swap)."""
    assert_frames_match(
        actual,
        expected,
        per_channel_tolerance=per_channel_tolerance,
        max_diff_ratio=0.0,
        swap_rb_on_actual=False,
        swap_rb_on_expected=False,
    )


def assert_qvgl_vs_qt_match(
    qvgl_png: Path,
    qt_png: Path,
    *,
    per_channel_tolerance: int = 12,
    max_diff_ratio: float = 0.05,
) -> None:
    """Compare QVGL/SDL dump against PyQt reference (swap BGR on QVGL side)."""
    assert_frames_match(
        qvgl_png,
        qt_png,
        per_channel_tolerance=per_channel_tolerance,
        max_diff_ratio=max_diff_ratio,
        swap_rb_on_actual=True,
        swap_rb_on_expected=False,
    )


def assert_frames_match(
    actual: Path,
    expected: Path,
    *,
    per_channel_tolerance: int = 1,
    max_diff_ratio: float = 0.0,
    swap_rb_on_actual: bool = False,
    swap_rb_on_expected: bool = False,
) -> None:
    diff, total = diff_pixel_count(
        actual,
        expected,
        per_channel_tolerance=per_channel_tolerance,
        swap_rb_on_actual=swap_rb_on_actual,
        swap_rb_on_expected=swap_rb_on_expected,
    )
    ratio = diff / total if total else 0.0
    assert ratio <= max_diff_ratio, (
        f"{diff}/{total} pixels differ ({ratio * 100:.2f}%), "
        f"max allowed {max_diff_ratio * 100:.2f}% (tol={per_channel_tolerance})"
    )
