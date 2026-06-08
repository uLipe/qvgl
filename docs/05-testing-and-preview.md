# 5. Testing and preview

## Philosophy

Generic pipeline proof at each stage; no hardware; no Qt install for default CI.

See [07-proof-of-correctness.md](07-proof-of-correctness.md).

## Tests (`tests/python/`)

| Area | Files |
|------|-------|
| IR | `test_ir_roundtrip.py`, `test_parser_ir_golden.py` |
| Parser reject | `test_parser_reject.py`, `test_conformance_manifest.py` |
| Emit | `test_hybrid_emit.py`, `test_emit_turbo_gauge.py`, `test_assets.py` |
| Render | `test_render_golden.py`, `test_gauge_ticks.py` |
| Animation | `test_arc_animation.py` |
| CLI | `test_qvglc_run_cli.py` |
| **C runtime** | `test_runtime_c.py` → `ctest` (see below) |

## C runtime test suite (R1 / R2)

Proof of **runtime semantics** and **generated setter contracts** — parallel to PNG goldens. Full plan: [12-runtime-data-plane.md](12-runtime-data-plane.md).

| Tier | Binary | Proves |
|------|--------|--------|
| **R1** `qvgl_runtime_unit` | No LVGL | `qvgl_map_linear_f32`, `qvgl_plot_*` pure helpers |
| **R2** `qvgl_emit_runtime` | Headless LVGL | Generated `ui_*.c` setters → real widget state |

```bash
cmake -B build -DQVGL_BUILD_TESTS=ON -DQVGL_LVGL_PATH=../lvgl
cmake --build build
ctest -R runtime --test-dir build
pytest tests/python/test_runtime_c.py
```

## Preview (`qvgl_preview`)

```bash
qvglc run examples/turbo_gauge/turbo_gauge.qml --set pressure=0 --headless --exit
```

Flags: `--headless`, `--set NAME=FLOAT`, `--frames`, `--dump-fb`, `--loop-frames`, `--exit`.

## CI

`.github/workflows/ci.yml` — `pytest tests/python` + LVGL at `../lvgl`.
