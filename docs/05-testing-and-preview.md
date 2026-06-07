# 5. Testing and preview

## Philosophy

Tests exist from **day 1** so each pipeline stage can land independently. No hardware required for default CI.

**Proof-of-correctness strategy (goldens per stage, render E2E, parser chain):** see [07-proof-of-correctness.md](07-proof-of-correctness.md).

## Layers

### Unit

| Module | Fixture | Assertion |
|--------|---------|-----------|
| `qvglc/ir` | hand-built node table | round-trip binary → parse → equal |
| `qvglc/parser` (planned) | `.qml` snippet files | token stream / AST golden |
| `qvglc/emit_lvgl` | `turbo_gauge.qvglir` | substring / symbol presence |

Runner: `tests/harness/qvgl_test.h` (minimal macros, zero external deps).

### Integration

Full path for one module:

```text
turbo_gauge.qml → qvglir → emit → gcc -c ui_turbo_gauge.c → render golden PNG
```

With:

- real LVGL from `QVGL_LVGL_PATH` for compile and render tests.

Golden files:

- `examples/turbo_gauge/golden/generated/` — emitted C/H
- `examples/turbo_gauge/golden/frames/` — render PNGs

### Preview (SDL)

Target: `qvgl_preview`

- Links **real LVGL** + generated UI (`turbo_gauge` does not link `qvgl_runtime`).
- Display path mirrors MCU intent:
  - **Draw buffer:** `LV_COLOR_FORMAT_ARGB8888`
  - **Present:** convert to **RGB565** for SDL texture (simulates panel)

Commands:

```bash
qvglc emit examples/turbo_gauge/golden/turbo_gauge.qvglir.json -o build/gen --lvgl-path ../lvgl
./build/qvgl_preview build/gen
```

Interactive checks:

- click area fires registered handler (log or toggle)
- `set_pressure()` updates arc + label

CI headless (smoke):

```bash
SDL_VIDEODRIVER=dummy ./build/qvgl_preview build/gen --frames 60 --exit
```

Render golden (headless framebuffer compare): see [07-proof-of-correctness.md](07-proof-of-correctness.md#render-golden-phase-4).

## CI matrix

| Job | Runs |
|-----|------|
| `test` (`.github/workflows/ci.yml`) | `pytest tests/python` + LVGL + headless preview renders |

Planned later: split `integration` (emit + `gcc -c`) and optional upstream sync job.

## Coverage CLI

`qvglc coverage file.qml --profile ultralite_v1` prints profile matrix and exits non-zero if unsupported features are used — same rules as sema, but report-only for designers.
