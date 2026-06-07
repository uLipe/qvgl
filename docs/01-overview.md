# 1. Overview

## Problem

Automotive and industrial UIs are often designed in **Qt Quick (QML)** with Qt Creator preview. Shipping on MCUs with **Qt for MCUs** has licensing and footprint cost. **LVGL** is a strong runtime on ESP32-class hardware but has no QML front-end.

## QVGL goal

Provide a **static compiler** that:

1. Accepts a **documented QML subset** (profile), aligned with *Qt Quick Ultralite* philosophy — not full Qt Quick.
2. Produces **self-contained C** (`ui_*.c/h`), a tiny **runtime** for dynamic bindings/handlers, and optional **LVGL config fragments**.
3. Keeps **Qt Creator** as the visual design reference; validation uses **tests + LVGL SDL preview** on the host.

## Non-goals (v1)

- Full Qt Quick / JavaScript compatibility
- QML runtime on device
- ShaderEffect, Canvas, ListView/Repeater at scale
- IDF component packaging (later); v1 is host CMake + drop-in `generated/`

## Primary PoC

**Turbo pressure gauge** (−0.7 … 2.0 bar):

- Designed in Qt Creator (reference screenshot)
- `onClicked` handler → app callback symbol
- `qvgl_turbo_gauge_set_pressure()` → updates arc + label via observers

## Success criteria (PoC)

| Check | Method |
|-------|--------|
| Parse + validate QML | unit + `qvglc validate` |
| IR round-trip | unit |
| Emit compiles | integration (host stub + real LVGL) |
| Looks correct | SDL preview (ARGB8888 draw, RGB565 present) |
| Runs on P4 | copy `generated/` into `esp32p4_qvgl_shell` |
