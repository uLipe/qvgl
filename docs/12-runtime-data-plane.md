# 12. Runtime data plane — plan & Passo 1 outline

Forward-looking implementation plan for the **Qt Creator → MCU** mission after static emit coverage (Controls, Layouts, `LinePlot` chrome). Complements [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md) and [09-roadmap.md](09-roadmap.md).

**Thesis:** QML stays declarative; **dynamic behavior lives in C** via a **layered runtime** (generic → specific). Generated `ui_*.c` only creates layout and calls runtime APIs. Proof uses a **dedicated C runtime test suite** alongside existing Python goldens.

---

## Runtime layer cake (coverage-first)

Scalable model for all Ultralite / Controls types that need live updates — not one runtime file per demo.

```text
┌─────────────────────────────────────────────────────────────┐
│ L3  Generated ui_<module>.c/h                             │
│     create, layout, thin setters → call L1/L2 only        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ L2  Domain widgets (one module per QML type with dynamics) │
│     qvgl_plot.c    LinePlot / lv_chart, domain, cursor     │
│     qvgl_arc.c     Arc value, ticks, animation helpers      │
│     qvgl_controls.c ToolButton, toggle, focus (future)    │
│     qvgl_image.c   src swap, visibility bundles (future)    │
└───────────────────────────┬─────────────────────────────────┘
                            │ uses
┌───────────────────────────▼─────────────────────────────────┐
│ L1  qvgl_widget.c — generic lv_obj operations               │
│     set_text, set_visible, set_opa, set_arc_value, …        │
│     Shared by every L2 module and by simple property setters│
└───────────────────────────┬─────────────────────────────────┘
                            │ uses
┌───────────────────────────▼─────────────────────────────────┐
│ L0  qvgl_runtime.c — no widget types                        │
│     qvgl_map_linear_f32, init, shared error/scale helpers   │
└─────────────────────────────────────────────────────────────┘
```

### Design rules

| Rule | Rationale |
|------|-----------|
| L2 **never** duplicates L1 LVGL calls | One place to fix label/visibility semantics |
| `ui_*.c` **never** grows business logic | Stays regeneratable; logic in runtime |
| New dynamic QML type → **new L2** (or extend existing L2), not `foo_card.c` | Matrix coverage stays general |
| L2 exposes a **context struct** (`qvgl_plot_t`, …) stored in `ui_*_t` | Emit wires pointers at create time |
| L0 functions are **pure** where possible | R1 tests without LVGL |
| Each L2 gets **R1 (math) + R2 (LVGL)** tests | Proof scales with coverage |

### Reference: `LinePlot` → `qvgl_plot.c`

| Concern | Layer | API (target) |
|---------|-------|----------------|
| Axis number formatting | L0/L2 | `qvgl_plot_format_axis` (today in L2; may share with L1 string format later) |
| Y domain from points | L2 | `qvgl_plot_compute_domain` |
| Push series to chart | L2 | `qvgl_plot_set_points(qvgl_plot_t *, const qvgl_plot_point_t *, n)` |
| Axis range + label refresh | L2 | `qvgl_plot_set_domain(...)` |
| Crosshair + footer text | L2 | `qvgl_plot_set_cursor(...)` |
| Create chart chrome | L3 emit | `qvgl_ui_*_create` builds `qvgl_plot_t` fields |
| Module property `points` | L3 setter | `qvgl_ui_*_set_*` → calls `qvgl_plot_set_points` |

Future `Arc` live updates: migrate arc value/tick logic from inline hybrid emit into **`qvgl_arc.c`** (L2), calling **`qvgl_widget_set_arc_value`** (L1).

### Target `runtime/` layout

```text
runtime/
  CMakeLists.txt          # qvgl_runtime STATIC: all .c below
  qvgl_runtime.c          # L0
  qvgl_widget.c           # L1 (Passo 1)
  qvgl_plot.c             # L2 (exists; grow in Passo 2)
  qvgl_arc.c              # L2 (later; consolidate gauge paths)
include/qvgl/
  qvgl_runtime.h
  qvgl_widget.h
  qvgl_plot.h
  qvgl_arc.h              # later
```

### Mapping Ultralite / Controls → runtime (living)

| QML type | Dynamic needs | L2 module | L1 ops used |
|----------|---------------|-----------|-------------|
| `Text` / `Label` | `text` binding | — (setter → L1) | `set_text` |
| `Rectangle` / `Item` | `visible`, `opacity` | — | `set_visible`, `set_opa` |
| `Arc` | `value`, animation | `qvgl_arc` | `set_arc_value` |
| `Image` | `source`, visible | `qvgl_image` 🔮 | `set_visible`, image src |
| `LinePlot` | points, domain, cursor | `qvgl_plot` | `set_text` on axis labels |
| `ToolButton` | enabled, checked 🔮 | `qvgl_controls` | `set_visible`, `set_text` |
| `MouseArea` | pressed state 🔮 | — or `qvgl_input` | event → app callback |

Empty L2 cell means **generated setter calls L1 directly** — still no raw LVGL scattered in emit.

---

## Where we are

| Layer | Status |
|-------|--------|
| Parse / sema / layout / static emit | ✅ HMIs, Controls, `LinePlot` static series |
| Hybrid emit | ✅ `property real` → `Arc` / `Text` setters (`float` only) |
| Runtime helpers | ✅ `qvgl_map_linear_f32`, `qvgl_plot_format_axis`, `qvgl_plot_compute_domain` |
| Plot interaction | ✅ `qvgl_plot_set_points` / `set_domain` / `set_cursor` (L2) |
| MCU integration shell | 📋 Passo 3 — **outside QVGL** (`esp32p4_qvgl_shell`) |

---

## Phased plan (mission order)

### Passo 1 — Unified property bindings (this document § Passo 1 outline)

Generate typed setters from module `property` + IR bindings; cover `real`, `int`, `bool`, `string` and keys `text`, `value`, `visible`, `opacity`.

**Exit:** example `bound_props_card` + C/LVGL setter tests + preview `--set` for all types.

### Passo 2 — Dynamic `LinePlot` (extend L2 `qvgl_plot.c`)

Grow **L2 only** — no plot logic in `ui_line_plot_card.c`:

- `qvgl_plot_t` context struct (chart, series, axis label refs) in `ui_*_t`
- `qvgl_plot_set_points`, `qvgl_plot_set_domain`, `qvgl_plot_set_cursor`
- L1 `qvgl_widget_set_text` for axis label refresh

**Exit:** R1 domain tests + R2 chart state tests + preview synthetic series.

### Passo 3 — MCU delivery loop (platform repo only)

**Not in QVGL tree.** Reference: `esp32p4_qvgl_shell/` (sibling ESP-IDF project, target `esp32p4`).

- `scripts/compile_ui.sh` → `generated/ui_*.c` from host `qvglc`
- IDF component links `qvgl/runtime` + generated UI + LVGL + BSP
- `app_main`: display port, `lv_timer` → `qvgl_ui_*_set_plot_points` (sine demo)

**Exit:** flash + monitor shows live plot ≥10 Hz. QVGL doc: [06-integration-shell.md](06-integration-shell.md).

### Passo 4 — Input polish

`MouseArea` pressed/released, handler table from QML (lower priority).

### Passo 5 — Visual polish (parallel when blocked)

`horizontalAlignment`, `PreserveAspectCrop`, `GridLayout`, typography.

### Passo 6 — Upstream validation (I8)

Trim Qt for MCUs demo QML; gaps → generic Passo 1–5 items.

---

## C runtime test suite (proof of truth)

Parallel to Python pipeline goldens ([07-proof-of-correctness.md](07-proof-of-correctness.md)). **Python proves compile/layout/render; C proves runtime semantics and generated setter contracts.**

### Two tiers

| Tier | Target | LVGL | What it proves |
|------|--------|------|----------------|
| **R1 — `qvgl_runtime_unit`** | `runtime/*.c`, `include/qvgl/*.h` | No | Pure math/string: `qvgl_map_linear_f32`, `qvgl_plot_format_axis`, `qvgl_plot_compute_domain`, future binding helpers |
| **R2 — `qvgl_emit_runtime`** | Generated `ui_*.c` from fixture QML | Yes (headless) | After `lv_init` + `create`: setters update the right LVGL state (label text, arc angle, `HIDDEN`, opacity) |

### Layout (to add)

```text
tests/
  harness/
    qvgl_test.h              # existing macros
  runtime/
    main.c                   # dispatches R1 cases
    test_map_linear.c
    test_plot_domain.c
  runtime_lvgl/
    main.c                   # lv_init, run R2 cases, lv_deinit
    test_bound_setters.c     # Passo 1
    test_plot_dynamic.c      # Passo 2
    fixtures/                # committed or CMake-generated ui_*.c/h
      bound_props_card/
  python/
    test_runtime_c.py        # pytest → ctest / direct exec
```

### CMake / CI

```cmake
# tests/CMakeLists.txt
add_executable(qvgl_runtime_unit ...)      # links qvgl_runtime only
add_test(NAME runtime_unit COMMAND qvgl_runtime_unit)

add_executable(qvgl_emit_runtime ...)      # links qvgl_runtime, lvgl, fixture ui_*.c
add_test(NAME emit_runtime COMMAND qvgl_emit_runtime)
```

- `QVGL_BUILD_TESTS=ON` (default): both tiers build and register with CTest.
- CI: `ctest` after `pytest` (or `pytest tests/python/test_runtime_c.py` wrapper).
- **No SDL** required for R2 — same headless LVGL config as preview.

### R2 assertion style (Passo 1)

Headless tests call generated API directly:

```c
qvgl_ui_bound_props_card_t ui;
qvgl_ui_bound_props_card_create(lv_screen_active(), &ui);
qvgl_bound_props_card_set_alarm(&ui, true);
/* assert lv_obj_has_flag(ui.indicator, LV_OBJ_FLAG_HIDDEN) == false */
qvgl_bound_props_card_set_title(&ui, "Ia");
/* assert strcmp(lv_label_get_text(ui.title_label), "Ia") == 0 */
```

Prefer **LVGL introspection** (`lv_label_get_text`, `lv_arc_get_value`, flags) over PNG compares for setter tests (faster, deterministic).

### Python glue

`test_runtime_c.py`:

- Builds `qvgl` with `-DQVGL_BUILD_TESTS=ON`
- Runs `ctest -R runtime` or binaries directly
- Fails CI if C proof regresses independently of PNG goldens

### Proof matrix (runtime column)

| Capability | R1 unit | R2 emit+LVGL | Python (existing) |
|------------|---------|--------------|-------------------|
| `qvgl_plot_format_axis` | ✅ | — | — |
| `qvgl_plot_compute_domain` | ✅ | — | — |
| `set_pressure` → arc+label | — | ✅ turbo fixture | `test_hybrid_emit.py` |
| `set_*` int/bool/string | — | ✅ Passo 1 | emit snapshot tests |
| `set_points` / `set_domain` | partial | ✅ Passo 2 | preview + optional PNG |

---

## Passo 1 outline — unified property bindings

**Goal:** One module can declare multiple `property` types; each bound field gets a typed `qvgl_<module>_set_<name>()`; app/preview drives UI like Qt for MCUs bindings.

**Reference today:** `bound_label.qml`, `turbo_gauge.qml`, `bindings_codegen.py`, `hybrid_ui.py`.

### 1.1 Contract (public API)

For module `bound_props_card` with:

```qml
Item {
    property real level
    property int channel
    property bool alarm
    property string title
    // bindings on children...
}
```

Emit in `ui_bound_props_card.h`:

```c
void qvgl_bound_props_card_set_level(qvgl_ui_bound_props_card_t * ui, float level);
void qvgl_bound_props_card_set_channel(qvgl_ui_bound_props_card_t * ui, int32_t channel);
void qvgl_bound_props_card_set_alarm(qvgl_ui_bound_props_card_t * ui, bool alarm);
void qvgl_bound_props_card_set_title(qvgl_ui_bound_props_card_t * ui, const char * title);
void qvgl_bound_props_card_sync(qvgl_ui_bound_props_card_t * ui);  /* optional: replay all from struct */
```

Struct fields mirror properties (typed, not all `float`).

Preview shim: extend `qvgl_preview_set_property` **or** add `qvgl_preview_set_property_str` / `_bool` for CLI tests.

### 1.2 IR / sema (minimal)

- `ModuleProperty.type` already `f32` / `i32` / `bool` / `str` from parser — verify hybrid path reads it.
- Bindings: allow `text: title` where `title` is `string` (`sym` only, no format).
- Allow `visible: alarm`, `opacity: level` only if types match or define promotion rules (bool → visible, real 0..1 → opacity).

**Files:** `ir_builder.py` (if gaps), `sema.py` (binding type check), `ir/model.py` (no change expected).

### 1.3 L1 — `qvgl_widget.c` (new, before widening emit)

Introduce L1 so setters and L2 modules share one implementation:

```c
void qvgl_widget_set_text(lv_obj_t * label, const char * text);
void qvgl_widget_set_visible(lv_obj_t * obj, bool visible);
void qvgl_widget_set_opa(lv_obj_t * obj, lv_opa_t opa);
void qvgl_widget_set_arc_value(lv_obj_t * arc, float value, float min, float max);
```

- R2 tests: create bare `lv_label` / `lv_arc`, call L1, assert state.
- Refactor existing hybrid arc path to call `qvgl_widget_set_arc_value` when touching bindings.

**Files:** `runtime/qvgl_widget.c`, `include/qvgl/qvgl_widget.h`, `tests/runtime_lvgl/test_widget.c`.

### 1.4 `bindings_codegen.py`

| Property type | Param | Consumer keys | Runtime call |
|---------------|-------|---------------|--------------|
| `f32` | `float` | `value` (Arc) | `qvgl_widget_set_arc_value` or `qvgl_arc_set_value` (L2) |
| `f32` | `float` | `text` (format/sym), `opacity` | L1 `set_text` / `set_opa` |
| `i32` | `int32_t` | `text` (sym) | L1 `set_text` via snprintf buf |
| `bool` | `bool` | `visible` | L1 `set_visible` |
| `str` | `const char *` | `text` | L1 `set_text` |

- Split `emit_setter_body` by `ModuleProperty.type`.
- Store typed field in `ui` struct: `float level`, `int32_t channel`, `bool alarm`, `char title[64]`.
- **No direct `lv_*` in generated setters** except in `create` — only L1/L2 calls.

**Files:** `qvglc/emit_lvgl/bindings_codegen.py`, `hybrid_ui.py` (fields + init_setters).

### 1.5 `hybrid_ui.py` integration

- Route `Label` (Text) through hybrid emit (today hybrid may not support Label from Controls-only modules — extend or use `Text`).
- Support `ColumnLayout` / `RowLayout` / `ToolButton` in hybrid **or** keep Passo 1 example anchor-only (simplest: `bound_props_card` without Layouts first).
- Apply `_rel_pos` from static emit (hybrid still uses absolute coords in some paths — fix if touched).

**Recommendation:** Passo 1 example = **flat anchors** (`bound_props_card`) to limit scope; Passo 1b = same bindings on `line_plot_card` `cursorLabel` (`property string`).

### 1.6 Example & conformance

**New:** `examples/bound_props_card/bound_props_card.qml`

- `property real level` → Arc or bar placeholder
- `property bool alarm` → `Rectangle` / `Image` `visible: alarm`
- `property string title` → `Label.text: title`
- `property int channel` → `Label` with `text: channel` (sym binding)

Golden: `golden/bound_props_card.qvglir.json` (optional), manifest tier `pass`.

### 1.7 C runtime tests (Passo 1 deliverable)

**R1** (split from `smoke.c`):

- `tests/runtime/test_plot_domain.c` — domain edge cases (empty points, single y, time window).
- Keep `test_map_linear.c` / small `main.c`.

**R2** (new):

- CMake: compile fixture `examples/bound_props_card` → `tests/runtime_lvgl/fixtures/bound_props_card/` (script in `test_runtime_c.py` pre-step or committed generated C).
- `test_bound_setters.c`: create UI, call each setter, assert LVGL state.
- Cases:
  - `set_alarm(true/false)` ↔ hidden flag
  - `set_title("x")` ↔ label text
  - `set_level(f)` ↔ arc value (if bound)
  - `set_channel(n)` ↔ label text

### 1.8 Python tests

| Test | Purpose |
|------|---------|
| `test_bindings_emit.py` | Generated C contains typed setters + struct fields |
| `test_runtime_c.py` | Invokes `qvgl_runtime_unit` + `qvgl_emit_runtime` |
| Extend `test_hybrid_emit.py` | No regression on `turbo_gauge` float path |

### 1.9 Docs & matrix

- [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md): `int`/`bool`/`string` emit ✅ when done.
- [05-testing-and-preview.md](05-testing-and-preview.md): R1/R2 table.
- [07-proof-of-correctness.md](07-proof-of-correctness.md): runtime stage row.

### 1.10 Commit order (suggested)

1. `test(runtime): split R1 unit suite from smoke; add test_runtime_c pytest`
2. `feat(runtime): add L1 qvgl_widget + R2 test_widget`
3. `feat(bindings): typed module property fields in hybrid ui struct`
4. `feat(bindings): emit setters via qvgl_widget_* (int/bool/string/real)`
5. `feat(examples): bound_props_card with conformance + R2 setter tests`
6. `feat(preview): preview shim string/bool property hooks for CLI`
7. `docs: runtime layer cake and matrix updates`

### 1.11 Out of scope (Passo 1)

- `ListView`, `Connections`, JS functions
- `LinePlot` dynamic points (Passo 2)
- `ternary` / `map_linear` in bindings (Passo 1b or I4)
- Full Controls in hybrid modules (static-only Controls OK elsewhere)

### 1.12 Done criteria (Passo 1)

- [ ] `qvglc check examples/bound_props_card/bound_props_card.qml` passes
- [ ] `ctest -R runtime` green (R1 + R2)
- [ ] `pytest tests/python/test_runtime_c.py` green
- [ ] `qvgl_preview --gen-dir ... --set level=0.5` still works on `turbo_gauge`
- [ ] Matrix rows for `property int/bool/string` marked ✅ at Emit

---

## After Passo 1

Proceed to **Passo 2** (`LinePlot` dynamic) using the same R1/R2 split: domain math in R1, chart point count/range in R2 with a minimal generated `line_plot_live` fixture.
