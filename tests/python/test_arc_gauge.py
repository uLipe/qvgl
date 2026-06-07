from __future__ import annotations

from qvglc.emit_lvgl.arc_gauge import plan_arc_gauge


def test_turbo_gauge_reverse_mode():
    p = plan_arc_gauge(
        from_deg=210,
        to_deg=-30,
        min_value=-0.7,
        max_value=2.0,
        line_width=24,
        color="#ff00d4aa",
        initial_value=-0.7,
        scale=10,
    )
    assert p.bg_start == 210
    assert p.bg_end == 330
    assert p.mode == "LV_ARC_MODE_REVERSE"
    assert p.min_i32 == -7
    assert p.max_i32 == 20


def test_normal_sweep():
    p = plan_arc_gauge(
        from_deg=0,
        to_deg=90,
        min_value=0,
        max_value=100,
        line_width=8,
        color="#ffffffff",
        initial_value=0,
        scale=1,
    )
    assert p.mode == "LV_ARC_MODE_NORMAL"
