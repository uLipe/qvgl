# 1. Overview

## Problem

UIs are often designed in **Qt Quick (QML)** with Qt Creator. Shipping on MCUs with **Qt for MCUs** has licensing and footprint cost. **LVGL** is a strong embedded runtime but has no QML front-end.

## QVGL goal

**Primary workflow:** design in **Qt Creator** (QML), preview with desktop Qt, ship on MCU with **LVGL** — without **Qt for MCUs** license or runtime. See [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md) for what to keep vs trim.

A **static compiler** that:

1. Accepts QML against a single documented subset (`profiles/ultralite_v1.yaml`).
2. Produces self-contained LVGL C (`ui_*.c/h`) and config fragments.
3. Validates on the host via **pytest**, **PyQt parity**, and **headless SDL preview**.

Input: trimmed QML model. Output: LVGL UI. No domain-specific layers in the toolchain.

## Non-goals (in-tree)

- QML runtime on device
- Full Qt Quick / JavaScript compatibility
- Automotive CAN, vehicle state, or cluster-specific codegen
- Multiple competing profiles — one subset, extended only when the generic compiler needs it

## Long-term validation target (out of tree)

Eventually QVGL should compile **upstream Qt MCUs vehicle demo QML** into an LVGL UI testable in SDL, with pixel-semantic parity. That work validates the generic compiler against real Qt output — it does **not** add vehicle APIs, bindings, or cluster profiles to this repository.

## Reference examples

| Example | Exercises |
|---------|-----------|
| `mcu_minimal` | upstream minimal green screen |
| `turbo_gauge` | bound `Arc`, handler, format label |
| `bound_label` | `property real` → `Text` setter |
| `static_card` / `icon_row` | static layout, borders, PNG assets |
| `gauge_ticks` / `arc_animated` | ticks, needle animation |
| `themed_chip` | `Theme.*` tokens at compile time |

## Success criteria (host)

| Check | Method |
|-------|--------|
| Parse + reject unsupported QML | `qvglc check`, conformance manifest |
| QML → IR | per-example `.qvglir.json` goldens |
| Emit vs LVGL 9+ | hybrid/static emit tests |
| Visual | headless PNG goldens |
| CI | `.github/workflows/ci.yml` |
