# 7. Proof of correctness

Golden-based checks per pipeline stage. [05-testing-and-preview.md](05-testing-and-preview.md) for harness layout.

## Pipeline

```text
QML → IR → emit C → qvgl_preview → PNG golden
                    ↘ C runtime suite (R1 helpers, R2 setter contracts)
```

See [12-runtime-data-plane.md](12-runtime-data-plane.md) for R1/R2 layout and Passo 1–2 plan.

## Stage matrix

| Stage | Status |
|-------|--------|
| IR codec | done |
| Parser reject fixtures | done |
| QML → IR goldens | done — `examples/*/golden/*.qvglir.json` |
| Static + hybrid emit | done |
| Render PNG goldens | done — turbo, minimal, gauge_ticks, icon_row, … |
| Conformance manifest | done — `qvglc conformance` |
| `qvglc proof` gate | done — conformance + emit markers + `qt_parity.yaml` + `reference_trim.yaml` |
| `qvglc run` CLI | done |
| Qt parity (optional) | done — `test_qt_parity_render.py` (`channel_plot_trim_qt.qml`) |
| C runtime R1 (unit) | done — `runtime_unit` |
| C runtime R2 (emit+LVGL) | done — `runtime_lvgl_*` split |
| CI GitHub Actions | done — `qvglc proof` + pytest + ctest |

## Render goldens (committed)

| Module | Exercises |
|--------|-----------|
| `turbo_gauge` | arc + label at pressure snapshots |
| `mcu_minimal` | baseline rectangle |
| `gauge_ticks` | `lv_scale` |
| `icon_row` | PNG embed |

Static modules: no mid-animation PNG unless frame count pinned to completion.

## Proof gate (CI)

```bash
qvglc proof    # manifest tiers + emit_markers + qt_parity schema + reference_trim
pytest tests/python/test_proof.py
pytest tests/python/test_conformance_emit.py
pytest tests/python/test_qt_parity_render.py   # optional: pip install -e ".[qt-parity]"
```

## Principles

1. Semantic equality (normalized IR, PNG buffers).
2. LVGL is render truth; Qt Creator advisory.
3. Self-contained generated `ui_*.c`.

## Changelog

| Date | Change |
|------|--------|
| 2025-05-28 | IR, parser, render E2E; generic examples |
| 2025-05-28 | Assets, theme, ticks, animation; CI |
| 2025-05-28 | Removed in-tree vehicle/cluster domain; single profile |
