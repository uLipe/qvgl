# 14. Sprint — Qt for MCUs parity (post-Controls)

Living plan after [13-sprint-roadmap.md](13-sprint-roadmap.md) phases 1–8 (Controls + proof gate). **Goal:** measure and close the gap between *design in Qt Creator / Qt for MCUs examples* and *deploy on LVGL via QVGL* without a commercial Ultralite license.

**Related:** [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md), [08-upstream-examples.md](08-upstream-examples.md), [07-proof-of-correctness.md](07-proof-of-correctness.md).

**Git:** commits on `main` only.

**Gate:** `qvglc proof` + example + pytest before marking a row ✅ in the matrix.

---

## Executive summary (current state)

### How close is QVGL to Qt for MCUs?

| Dimension | Proximity | Notes |
|-----------|-----------|-------|
| **Workflow** (Creator → MCU) | **~70%** | Same QML *syntax* for a trimmed subset; not the same runtime or module set |
| **Static screens** (cards, labels, icons, layouts) | **~90%** | `mcu_minimal`, `static_card`, `controls_card`, flex layouts |
| **Controls** (Qt Quick Controls) | **~75%** | P0–P2 done; no `TextField`, `ScrollView`, `StackView`, delegates |
| **Gauges** (Studio / `ArcItem`) | **~50%** | `turbo_gauge` / `gauge_ticks` are **derivatives**, not compile of official `Gauge.qml` |
| **Plots / charts** | **~60%** | QVGL `LinePlot` replaces `Canvas`; live data via C L2 |
| **Upstream examples (pass tier)** | **1 file** | `minimal.qml` compiles as-is; rest needs trim or is `reject` |
| **Full cluster / vehicle QML** | **~15%** | Reference-only; trim manifest not started |

QVGL is **not a drop-in Qt for MCUs runtime**. It is a **compile-time path**: trimmed QML → static LVGL C + thin C setters. Designers keep Qt Creator; integrators run `qvglc check` / `qvglc coverage` and move logic to C.

### Can I deploy a UI created for Qt for MCUs today?

**Partially yes**, with constraints:

| Scenario | Deploy today? | What you do |
|----------|---------------|-------------|
| Qt MCUs **`minimal`**-style screen (Rectangle + Text) | ✅ Yes | `qvglc compile` → link in `esp32p4_qvgl_shell` |
| Screen using **supported Controls + Layouts + Material colors** | ✅ Yes | Trim handlers to `app_on_*()`, static `ComboBox` model |
| Screen with **`Arc` gauge** (single arc, bound value) | ✅ Yes | See `turbo_gauge`; not dual-`ArcItem` Studio gauge |
| Screen with **live plot** | ✅ Yes | Use `LinePlot` + `PlotPoint`; feed series from C (`apply_plot_series`) |
| **Official Studio `Gauge.qml`** / `ArcItem` | ❌ No | Rewrite to `Arc` or `turbo_gauge` pattern |
| **`ListView` / `ListModel` / `Repeater`** | ❌ No | Static UI or app-driven refresh |
| **`Canvas` / `onPaint`** | ❌ No | `LinePlot` or custom LVGL in app |
| **JS `function` / `Math` / `property var`** | ❌ No | Move to C; use module `property` + setters |
| **`State` / `Behavior` / `Timer`** | ❌ No | Module properties + app tick |
| **Full automotive cluster** | ❌ No | Phase-out trim per screen; see Phase A below |

**Recommended loop:**

```text
Qt Creator (Qt for MCUs or desktop Qt kit)
    → qvglc check / qvglc coverage   (trim until green)
    → qvglc compile --mcu-root       (P4: esp32p4_1024x600 profile)
    → esp32p4_qvgl_shell / your IDF project
```

---

## What already matches Qt for MCUs (proof)

| Proof | Artifact |
|-------|----------|
| Upstream minimal | `examples/upstream/manifest.yaml` → `mcu_minimal` pass + SHA fixture |
| Conformance | `qvglc proof` — manifest + emit markers + `reference_trim` |
| Qt render parity (desktop Qt Quick) | `qt_parity.yaml` — 5 cases incl. `channel_plot_trim_qt.qml` |
| MCU deploy | `esp32p4_qvgl_shell` — `channel_plot_trim` @ 1024×600 + sine loop |
| Controls sprint | [13-sprint-roadmap.md](13-sprint-roadmap.md) phases 1–8 ✅ |

---

## Pending work (highest impact)

Grouped by *designer pain* when porting Qt for MCUs QML.

### P0 — Blockers for real HMIs (trim-heavy)

| Gap | Qt for MCUs habit | Target |
|-----|-------------------|--------|
| **Studio `Gauge.qml`** | `ArcItem`, gradients, timers | `tier: reference` trim doc + `turbo_gauge` parity checklist |
| **Comparison in bindings** | `checked: mode == 0` | Parser `==` or document “use bool properties” |
| **`ComboBox` dynamic model** | `ListModel` / C++ model | Static `model: [...]` only today |
| **Upstream pass expansion** | More than `minimal.qml` | Add 2–3 trimmed MCUs examples to `pass` tier |

### P1 — Ergonomics

| Gap | Target |
|-----|--------|
| `GridLayout` | Profile + flex emit |
| `horizontalAlignment` full emit | Text alignment in LVGL |
| `Image.PreserveAspectCrop` | `widget_style` / layout |
| `font.weight` tiers | Map bold → next Montserrat tier |
| Hybrid `Arc` responsive @ design resolution | Optional; goldens at fixed size |

### P2 — Input & navigation

| Gap | Target |
|-----|--------|
| `ScrollView` / flickable | `lv_obj` scroll + profile (large) |
| `StackView` / multi-page | Out of scope or app-level screen swap |
| `TextField` | Out of scope (keyboard) unless bare `lv_textarea` later |

### P3 — Validation (no new emit)

| Gap | Target |
|-----|--------|
| Automotive / vehicle QML | `tier: reference` entries + trim manifest per screen |
| Qt MCUs render vs LVGL | High-tolerance job on synced `Gauge.qml` snapshot |
| `test_upstream_examples` in CI | Optional job when `QTMCU` available |

### Explicit non-goals (this sprint)

- Qt for MCUs **runtime** or **LicenseRef-Qt-Commercial** code in-tree
- CAN / vehicle bindings / domain-specific profiles
- `ListView` with delegates
- Pixel-perfect identity with Qt MCUs preview for all screens

---

## Sprint phases (outline)

| Phase | Focus | Exit criteria |
|-------|--------|---------------|
| **A** | **Upstream trim catalog** | `reference_trim.yaml` lists 3+ MCUs derivatives; doc per screen “keep / trim / C” |
| **B** | **Studio gauge path** | Trim checklist `Gauge.qml` → `turbo_gauge`; optional PNG compare |
| **C** | **Binding ergonomics** | `==` / `!` in bindings OR matrix-doc bool-property pattern; `ComboBox` doc |
| **D** | **Layout P1** | `GridLayout` or `horizontalAlignment` emit — pick one |
| **E** | **Vehicle pilot** | One upstream cluster screen: `qvglc check` green after trim; P4 build |

Phases are **sequential A → B**; **C–E** parallel once A defines trim rules.

---

## Phase A — Upstream trim catalog (next)

1. Extend [examples/upstream/manifest.yaml](../examples/upstream/manifest.yaml):
   - `mcu_studio_gauge` → link to `turbo_gauge` trim notes
   - Add `mcu_automotive_*` as `reference` (paths only, no commit of QML)
2. Extend [examples/conformance/reference_trim.yaml](../examples/conformance/reference_trim.yaml):
   - `turbo_gauge` → `derives_from: mcu_studio_gauge`
   - `line_plot_card` → note “desktop card; not MCUs upstream”
3. Add `docs/trim-checklist.md` (single page): step-by-step Creator → QVGL
4. `qvglc proof` validates every `reference` id has `reference_trim` entry ✅ (already)

---

## Phase B — Studio gauge

1. Document field mapping: `ArcItem` outer/inner → single `Arc` + `lv_scale`
2. List rejected Studio features (gradient, animation timer)
3. Optional: sync `Gauge.qml` → manual PNG vs `turbo_gauge` preview (high tolerance)

---

## Phase C — Binding ergonomics

1. Parser: equality/`!` for `checked:` / `visible:` OR formalize bool module props pattern in matrix
2. Document `ComboBox` static-only constraint in Creator workflow section
3. R2 tests if new binding forms added

---

## Phase D — Layout P1

Pick **one** for next slice:

- **Option 1:** `GridLayout` (profile + layout pass)
- **Option 2:** `Text.horizontalAlignment` → `lv_label` align flags

---

## Phase E — Vehicle pilot (validation only)

1. Choose one screen from Qt MCUs `automotive/` or similar (reference tier)
2. Trim to `ultralite_v1`; no automotive APIs in QVGL
3. `qvglc compile` + manifest `pass` or `reference`
4. Gaps → generic issues in phases C/D only

---

## Proximity scorecard (track over sprints)

| Milestone | Target % | Metric |
|-----------|----------|--------|
| M0 (now) | — | 1 upstream `pass`; 5 qt_parity; Controls P2; P4 plot shell |
| M1 (after A) | +10% | 3 documented trims; all `reference` in `reference_trim.yaml` |
| M2 (after B) | +10% | Studio gauge checklist; designer can follow without reading emit code |
| M3 (after E) | +15% | 1 cluster screen compiles + P4 flash |

---

## Commands (designer + CI)

```bash
qvglc proof
qvglc check path/to/screen.qml
qvglc coverage path/to/screen.qml
qvglc compile path/to/screen.qml -o /tmp/gen --profile profiles/esp32p4_1024x600.yaml --mcu-root
pytest tests/python/test_upstream_examples.py   # needs sync_upstream_examples.sh
pytest tests/python/test_qt_parity_render.py      # optional PyQt6
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-28 | Initial sprint doc post Controls 1–8; proximity assessment |
