# 7. Proof of correctness

Design reference for golden-based testing across the QVGL pipeline. Each stage owns a **golden artifact** and a **deterministic check** that fails on semantic drift, not only on crashes.

**Related:** [05-testing-and-preview.md](05-testing-and-preview.md) (harness layout, SDL preview), [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md).

---

## Pipeline under test

```text
QML ──parser──▶ IR ──emit──▶ generated C ──LVGL render──▶ ARGB8888 framebuffer
 │               │                                    │
 │               └── golden .qvglir (structural)      └── golden PNG (visual)
 └── ≡ golden IR
```

A change that passes IR tests but breaks pixels is caught at **render golden**. A parser bug is caught when QML → IR ≠ committed IR, before emit runs.

---

## Principles

1. **Semantic equality, not text diff** — compare normalized IR dicts, token streams, AST dumps, and PNG buffers; never pretty-printed JSON or raw QML text.
2. **One golden per concern** — structural (IR), compile-time (emit substrings + `gcc -c`), visual (framebuffer PNG).
3. **Self-contained generated UI** — render tests link generated `ui_*.c` only; turbo gauge does not require `qvgl_runtime`.
4. **Determinism** — pin LVGL version, fixed `lv_conf`, fixed fonts, no animations, fixed frame count before framebuffer dump.
5. **LVGL is the render source of truth** — goldens capture the **ARGB8888 draw buffer** after `lv_timer_handler()` settles. RGB565 SDL conversion is display plumbing (unit-tested separately).
6. **Qt Creator is advisory** — useful to capture the first golden and manual review; CI goldens are LVGL self-consistent to avoid font/renderer skew.

---

## Stage matrix

| Stage | Golden location | Assertion | Status |
|-------|-----------------|-----------|--------|
| **IR codec** | `examples/turbo_gauge/golden/turbo_gauge.qvglir` (+ `.json`) | JSON → bin → decode → normalized `module_to_dict()` equality | done |
| **IR validate** | `tests/fixtures/ir_invalid/` (planned) | `validate()` error code + message | partial |
| **Emit** | `qvglc compile` → `ui_*.c` in build dir | substring markers + `gcc -c` vs real LVGL | done |
| **Render** | `examples/turbo_gauge/golden/frames/*.png` | headless LVGL buffer vs PNG per property snapshot |  |
| **Parser sema reject** | `tests/fixtures/qml/reject/` + `manifest.yaml` | stable `DiagnosticCode` per fixture | done |
| **Parser → IR** | `turbo_gauge.qml` vs golden IR | QML → IR ≡ golden (same normalizer as codec) | done |
| **Lexer** | `tests/fixtures/parser/*.tokens` | token stream equality |  |
| **AST** | `tests/fixtures/parser/*.ast` | AST dump equality |  |
| **Layout** | `resolve_layout(mod)` vs expected `Rect` map | anchor resolver golden per module | done |
| **Static emit** | `cluster_shell`, `instrument_cluster_static`, `mcu_minimal` | emit substring markers + `gcc -c` | done |
| **Cluster render** | `examples/cluster_shell/golden/frames/*.png`, `instrument_cluster_static` | headless LVGL buffer vs PNG | done |
| **Conformance tiers** | `examples/conformance/manifest.yaml` | `qvglc check` pass/reject per tier | done |
| **Image / opacity / fonts emit** | `test_assets.py`, `examples/icon_row/` | emit markers + render golden | done |
| **CLI `qvglc run`** | `test_qvglc_run_cli.py` | subprocess E2E: compile + LVGL/SDL preview per manifest `pass` | done |
| **Qt vs QVGL render parity** | `test_qt_parity_render.py` | PyQt offscreen grab vs SDL/LVGL dump; `examples/conformance/qt_parity.yaml` |  |

---

## IR semantic equality

Binary round-trip is necessary but not sufficient.

**Canonical check:** `module_to_dict(decode(encode(mod)))` compared to a normalized golden dict:

- Floats normalized (e.g. `%.6g`) to absorb f32 noise.
- Keys sorted stably for comparison.
- Full graph: nodes, properties, bindings, expr trees, handlers.

**Implementation:** `tests/python/test_ir_roundtrip.py` (existing).

**Invalid IR:** dedicated fixtures with expected `IrValidationError` messages (to add).

---

## Parser semantic equality

Reuse the **same IR normalizer** as codec tests.

```text
parse(qml) → build_ir(ast) → module_to_dict() ≡ module_to_dict(golden)
```

Lexer and parser stages use their own goldens before IR is built:

| Layer | Golden | Test |
|-------|--------|------|
| Lexer | `.tokens` file per snippet | byte-exact token stream |
| Parser | `.ast` JSON dump | structural AST equality |
| Sema | negative `.qml` snippets | diagnostic code + line |
| IR builder | full module | IR dict ≡ golden |

**Pipeline check:** `qvglc compile turbo_gauge.qml` produces IR that still passes render golden.

---

## Render golden

### End-to-end path

```text
turbo_gauge.qvglir → emit → link qvgl_preview → set_pressure(p) → lv_refr → dump ARGB8888 → PNG compare
```

### Golden frames (`turbo_gauge`)

Committed under `examples/turbo_gauge/golden/frames/`:

| File | `pressure` | What it exercises |
|------|------------|-------------------|
| `turbo_gauge_p-0.7.png` | −0.7 bar | arc at min, label text |
| `turbo_gauge_p0.0.png` | 0.0 bar | mid sweep |
| `turbo_gauge_p2.0.png` | 2.0 bar | arc at max |

Add frames when new bindings or widgets change visual output.

### Golden frames (`cluster_shell`, `instrument_cluster_static`)

Committed under `examples/cluster_shell/golden/frames/` and `examples/instrument_cluster_static/golden/frames/`:

| File | Profile | What it exercises |
|------|---------|-------------------|
| `cluster_shell.png` | `cluster_480x272` | multi-widget static frame, sibling anchors, gauge slots |
| `instrument_cluster_static.png` | `cluster_480x272` | Qt MCUs HUD trimmed (literal bindings), `centerIn` sibling |

**Tests:** `tests/python/test_cluster_examples.py` — IR, layout rects, emit markers, render PNG, `qvglc run --profile` headless.

### Harness CLI (planned)

```bash
./build/qvgl_preview build/gen \
  --headless \
  --pressure -0.7 \
  --frames 3 \
  --dump-fb /tmp/frame.raw
```

- `--headless` — no interactive window; `SDL_VIDEODRIVER=dummy` acceptable for smoke, framebuffer dump does not require a visible window.
- `--frames N` — run `lv_timer_handler()` N times after setup so layout and draw complete.
- `--dump-fb PATH` — write raw ARGB8888 (width × height × 4) or PNG directly.

### Pytest wrapper

`tests/python/test_render_golden.py`:

1. Emit into temp dir (or use committed `golden/generated/`).
2. Build or locate `qvgl_preview` binary.
3. Subprocess per pressure snapshot with `--dump-fb`.
4. Compare against committed PNG (exact match, or per-pixel tolerance ≤ 1 on antialiased arc edges).
5. On failure, write diff image to pytest temp dir for CI artifacts.

### RGB565 flush (separate test)

`tests/unit/test_sdl_flush.c` or pytest helper:

- Feed known ARGB8888 patch → run conversion → compare RGB565 bytes.
- Keeps SDL display path tested without coupling to gauge visuals.

---

## Determinism checklist (render CI)

- [ ] `QVGL_LVGL_PATH` pinned in CI to the same tree as local dev.
- [ ] `qvgl_lv_conf.h` from emit: fixed color depth, Montserrat 14/36, anti-alias flags documented.
- [ ] No `NumberAnimation` or async layout in modules under render golden.
- [ ] Fixed display size (400×400 for turbo gauge).
- [ ] `lv_tick_inc()` / timer cadence fixed in preview main loop.

---

## CI jobs (planned)

| Job | Scope |
|-----|--------|
| `unit` | C smoke + pytest IR / emit / arc_gauge |
| `integration` | emit + `gcc -c` generated UI |
| `render-golden` | headless framebuffer PNG compare |
| `preview-smoke` | `SDL_VIDEODRIVER=dummy --frames 60 --exit` |
| `parser-golden` | QML → IR ≡ golden |

---

## Failure diagnosis

| Symptom | Likely stage |
|---------|----------------|
| IR round-trip fails | codec / validate |
| `gcc -c` fails | emit / lvgl_probe |
| PNG mismatch, C compiles | emit mapping (arc angles, colors, layout) or LVGL version drift |
| QML → IR mismatch | parser / sema |
| IR OK, PNG OK after parser change | unlikely — pipeline is chained |

---

## Non-goals (v1)

- Pixel-perfect match against Qt Creator export in CI (manual / high-tolerance optional job only).
- Hardware framebuffer capture on ESP32-P4 ( is smoke boot, not PNG golden).
- Fuzz testing (post-PoC hardening).

---

## Changelog

| Date | Change |
|------|--------|
| 2025-05-28 | Initial strategy: IR + parser semantic goldens; ARGB8888 render E2E in  |
| 2025-05-28 | generic `emit_static`, cluster examples, layout + render goldens at 480×272 |
| 2025-05-28 | Image PNG embed, opacity/visible, profile font tiers; `test_assets.py` |
