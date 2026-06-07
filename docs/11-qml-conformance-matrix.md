# 11. QML conformance matrix (Qt Quick / Ultralite → QVGL → LVGL)

Living compatibility reference for **Qt Creator design flow** vs **what QVGL compiles today**. Use this to prioritize roadmap phases and to set expectations with upstream Qt for MCUs examples.

**Not a promise of pixel-perfect Qt runtime parity** — QVGL is static compile-time codegen to LVGL; the matrix tracks *semantic* support per layer.

**Related:** [profiles/ultralite_v1.yaml](../profiles/ultralite_v1.yaml), [08-upstream-examples.md](08-upstream-examples.md), [07-proof-of-correctness.md](07-proof-of-correctness.md).

---

## How to read the matrix

Each feature is scored at four layers:

| Layer | Question |
|-------|----------|
| **Profile** | Allowed in `ultralite_v1` / `cluster_480x272` YAML? |
| **Sema** | `qvglc check` accepts it? |
| **IR** | Lowered to IR bindings / properties? |
| **Emit** | Generates correct LVGL C? |

When a row is ✅ or ⚠️ at **Emit**, the **Proof** column points to the test file, example, or generated artifact that demonstrates real behavior (not profile declaration alone).

### Status legend

| Mark | Meaning |
|------|---------|
| ✅ | Works end-to-end (with tests or committed example) |
| ⚠️ | Partial — parses or emits with known gaps |
| 📋 | Profile only — declared but not implemented in emit |
| ❌ | Rejected by sema or out of scope v1 |
| 🔮 | Planned (roadmap phase) |
| 🧱 | LVGL / hardware limit — not a QML parser gap |

**Machine-checkable subset:** [examples/conformance/manifest.yaml](../examples/conformance/manifest.yaml) — pytest enforces `pass` / `reject` tiers on committed QML.

---

## Design principles (tool vs examples)

- **QVGL stays generic** — no automotive- or example-specific CLI/emit paths.
- **Qt Creator compatibility** is achieved by **profile + emit coverage**, not by forking QML per demo.
- **Upstream examples** are tiered: `pass`, `partial`, `reject`, `reference` (see [08-upstream-examples.md](08-upstream-examples.md)).
- **Majority Ultralite-compatible** means: common cluster/HMI screens compile after *documented trimming* (remove animations, C++ singletons, Studio-only types) — not zero-edit drop-in of every commercial demo.

---

## Imports

| Import | Profile | Sema | IR | Emit | Notes |
|--------|---------|------|-----|------|-------|
| `QtQuick 2.15` | ✅ | ✅ | ✅ | ✅ | Primary import |
| `QtQuick 2.0` | ✅ | ✅ | ✅ | ✅ | Alias |
| `QtQuick.Controls` | ❌ | ❌ | — | — | Desktop controls; not Ultralite |
| `QtQuickUltralite.Studio.Components` | ❌ | ❌ | — | — | Commercial Studio widgets (`Gauge`, `ArcItem`) |
| `QtQuickUltralite.Extras` | ❌ | ❌ | — | — | 🔮 optional profile extension |
| `QtQuick.Shapes` | ❌ | ❌ | — | — | 🧱 use Image or LVGL draw APIs |

---

## Types (Qt Quick Ultralite subset)

| QML type | Profile | Sema | IR | Emit → LVGL | Proof | Gap / phase |
|----------|---------|------|-----|-------------|-------|-------------|
| `Item` | ✅ | ✅ | ✅ | ✅ `lv_obj` | `test_cluster_examples.py` | Root / container |
| `Rectangle` | ✅ | ✅ | ✅ | ✅ `lv_obj` + style | `examples/static_card/`, `test_assets.py::test_border_emit_markers` | |
| `Text` | ✅ | ✅ | ✅ | ✅ `lv_label` | `test_assets.py::test_profile_font_tiers`, `instrument_cluster_static` render | `font.weight` ❌ |
| `Arc` | ✅ | ✅ | ✅ | ✅ `lv_arc` | `test_emit_turbo_gauge.py`, `test_dual_gauge.py` | Single arc, not dual `ArcItem` track+value |
| `Image` | ✅ | ✅ | ✅ | ✅ `lv_image` | `test_assets.py`, `examples/icon_row/` | `PreserveAspectFit` ✅; `PreserveAspectCrop` 📋 |
| `MouseArea` | ✅ | ✅ | ✅ | ✅ transparent `lv_obj` | `test_mcu_minimal.py` | `pressed`/`released` 📋 |
| `Meter` | ✅ | 📋 | ❌ | ❌ | Profile placeholder; use `Arc` + `tickCount` or `Meter` later |
| `ListView` | ❌ | ❌ | — | — | No model/view |
| `Repeater` | ❌ | ❌ | — | — | |
| `Timer` | ❌ | ❌ | — | — | Use app timer + setters |
| `NumberAnimation` | ❌ | ❌ | — | — | 🔮  subset |
| `Behavior` | ❌ | ❌ | — | — | |
| `State` / `PropertyChanges` | ❌ | ❌ | — | — | |
| `Connections` | ❌ | ❌ | — | — | |
| `Component` | ❌ | ❌ | — | — | No dynamic instantiation |

### Qt for MCUs Studio / commercial types

| Type | QVGL | Ultralite equivalent | Phase |
|------|------|----------------------|-------|
| `ArcItem` (dual layer) | ❌ | `Arc` × 1 → `lv_arc` bg+indicator | ⚠️ simplified PoC |
| `Gauge` (Studio) | ❌ | `turbo_gauge` / `cluster_dual_gauge` | reference only |
| `LinearGradient` | ❌ | flat `color` | 🔮 optional |
| `Theme` singleton | ⚠️ | `Theme.token` → profile color at compile time | `test_assets.py::test_theme_resolves_in_ir`, `examples/themed_chip/` | Not a runtime singleton |
| `VehicleStatus` (C++) | ❌ | `qvgl_vehicle_state_t` + `vehicle-bind` | `test_vehicle_model.py` — use module `property` or C apply, not QML singleton |

---

## Properties (high-traffic)

| Property | Profile | Sema | IR | Emit | Proof | Notes |
|----------|---------|------|-----|------|-------|-------|
| `width` / `height` | ✅ | ✅ | ✅ | ✅ | `test_cluster_examples.py` | Root + explicit sizing |
| `x` / `y` | ✅ | ✅ | ✅ | ⚠️ | `examples/icon_row/icon_row.qml` | Prefer anchors; absolute pos in layout |
| `visible` | ✅ | ✅ | ✅ | ✅ | `emit_lvgl/widget_style.py`, `test_assets.py::test_opacity_emit_hidden` | `LV_OBJ_FLAG_HIDDEN` |
| `opacity` | ✅ | ✅ | ✅ | ✅ | `test_assets.py`, `instrument_cluster_static` render golden | `0` → hidden; fractional → `lv_obj_set_style_opa` |
| `enabled` | ✅ | ✅ | ✅ | ✅ | `emit_lvgl/widget_style.py` | `lv_obj_clear_flag(CLICKABLE)` |
| `color` (#RGB/#ARGB) | ✅ | ✅ | ✅ | ✅ | `test_mcu_minimal.py` | Normalized to `#aarrggbb` in IR |
| `radius` | ✅ | ✅ | ✅ | ✅ | `test_cluster_examples.py` | |
| `border.width` / `border.color` | ✅ | ✅ | ✅ | ✅ | `test_border_emit_markers`, `examples/static_card/` | |
| `text` (literal) | ✅ | ✅ | ✅ | ✅ | `examples/static_card/` | |
| `text` (binding) | ✅ | ✅ | ✅ | ✅ | `test_dual_gauge.py` | `sym` or `format` only |
| `font.pixelSize` | ✅ | ✅ | ✅ | ✅ | `profiles/cluster_480x272.yaml` `fonts.tiers`, `test_assets.py::test_profile_font_tiers` | Profile tier map → Montserrat 14/36/48 |
| `font.weight` | ❌ | ❌ | — | — | — | Custom TTF 🔮 |
| `horizontalAlignment` | ✅ | ✅ | 📋 | ❌ | — | Emit uses align for anchored labels only |
| `source` / `fillMode` (`Image`) | ✅ | ✅ | ✅ | ✅ | `emit_lvgl/assets.py`, `test_fillmode_emit_preserve_aspect` | PNG embed; `Stretch` + `PreserveAspectFit` |
| Arc `from` / `to` / `minValue` / `maxValue` / `value` | ✅ | ✅ | ✅ | ✅ | `test_emit_turbo_gauge.py` | CCW sweep via `LV_ARC_MODE_REVERSE` |
| Arc `lineWidth` / `color` | ✅ | ✅ | ✅ | ✅ | `test_dual_gauge.py` | |
| Arc `tickCount` / `majorTickEvery` / `showTickLabels` | ✅ | ✅ | ✅ | ✅ | `emit_lvgl/arc_scale.py`, `test_gauge_ticks.py` | `lv_scale` ROUND_OUTER behind `lv_arc` |
| Arc `rotation` | ✅ | ⚠️ | 📋 | ❌ | — | 🔮 |

---

## Anchors (compile-time resolver)

| Anchor | Profile | Sema | Layout | Emit | Notes |
|--------|---------|------|--------|------|-------|
| `anchors.fill` | ✅ | ✅ | ✅ | ✅ | |
| `anchors.centerIn` | ✅ | ✅ | ✅ | ✅ | parent or sibling id |
| `anchors.top` / `bottom` / `left` / `right` | ✅ | ✅ | ✅ | ✅ | |
| `anchors.horizontalCenter` / `verticalCenter` | ✅ | ✅ | ✅ | ✅ | sibling `id.edge` forms |
| `anchors.margins` | ✅ | ✅ | ✅ | ✅ | uniform |
| `*Margin` (per-edge) | ✅ | ✅ | ⚠️ | ⚠️ | Negative margins approximate Qt |
| `anchors.baseline` | ❌ | ❌ | — | — | |
| Layout attached props (`Layout.fillWidth`) | ❌ | ❌ | — | — | Use nested `Item` + anchors |

---

## Module properties & bindings

| Feature | Profile | Sema | IR | Emit | Notes |
|---------|---------|------|-----|------|-------|
| `property real` / `int` / `bool` / `string` | ✅ | ✅ | ✅ | ⚠️ | Emit: `real` → setter; others 🔮 |
| `property var` | ✅ | ✅ | ✅ | ⚠️ | Treated as `f32` in IR |
| Binding `sym` (e.g. `value: speed`) | ✅ | ✅ | ✅ | ✅ | Arc + labels |
| `toFixed(n) + "suffix"` | ✅ | ✅ | ✅ | ✅ | Lowered to `format` in IR builder |
| Bare `toFixed(n)` | ⚠️ | ✅ | ⚠️ | ⚠️ | Use `toFixed(n) + ""` pattern |
| `a + b` (non-format) | ⚠️ | ⚠️ | ❌ | — | Only format-add pattern |
| `Math.*` / arbitrary JS calls | ❌ | ❌ | — | — | |
| `map_linear` | ✅ | 📋 | 📋 | 📋 | In profile; turbo uses inline mapping |
| `ternary` | ✅ | 📋 | 📋 | ❌ | |
| Division `/` | ❌ | ❌ | — | — | Precompute in C or use format |

---

## Signals & handlers

| Feature | Profile | Sema | IR | Emit | Notes |
|---------|---------|------|-----|------|-------|
| `MouseArea.onClicked` | ✅ | ✅ | ✅ | ✅ | Bare `app_*()` call only |
| Custom handler names | ⚠️ | ❌ | — | — | Whitelist today; 🔮 symbol table from QML |
| `onPropertyChanged` | ❌ | ❌ | — | — | |
| C++ singleton signals (`VehicleStatus.on*`) | ❌ | ❌ | — | — |  vehicle model |

---

## Expressions of compatibility (summary)

### What works today (representative Qt MCUs paths)

| Workflow | Example | Tier |
|----------|---------|------|
| Getting started green screen | `mcu_minimal/minimal.qml` | ✅ pass |
| Single dynamic gauge | `turbo_gauge/turbo_gauge.qml` | ✅ pass |
| Static cluster chrome | `cluster_shell/cluster_shell.qml` | ✅ pass |
| Trimmed instrument HUD | `instrument_cluster_static.qml` | ✅ pass |
| Icon row (PNG assets) | `icon_row/icon_row.qml` | ✅ pass |
| Dual bound gauges | `cluster_dual_gauge/cluster_dual_gauge.qml` | ✅ pass |

### What requires trimming from official Qt MCUs QML

| Official feature | Action for QVGL |
|------------------|-----------------|
| `Behavior` / `NumberAnimation` | Remove; use static values or C-side updates |
| `VehicleStatus.*` | Replace with literals or module `property` + app setters |
| `font.weight` | Not supported; use nearest Montserrat tier |
| `ArcItem` / Studio `Gauge` | Rewrite as `Arc` + `Text` or keep as reference |
| `Image` telltales | Use `Image { source: "assets/..." }` — PNG embedded at compile time |

### What LVGL offers beyond current emit (opportunities)

| LVGL 9 widget | Ultralite analogue | QVGL status |
|---------------|-------------------|------------|
| `lv_scale` (round) | tick marks, dial labels |  |
| `lv_image` | `Image`, telltales | ✅ `examples/icon_row/` |
| `lv_label` long mode / styles | wrapped text, dimmed telltales |  |
| `lv_obj` opacity / hidden | `opacity`, `visible` | ✅ `widget_style.py` |
| `lv_button` / `lv_imagebutton` | touch targets | 🔮 if profile adds types |

---

## Gap analysis → roadmap priority

Priority for **majority Ultralite-shaped HMI** (cluster, gauge, status strip):

| Priority | Gap | Blocks | Status |
|----------|-----|--------|--------|
| ~~P0~~ | ~~`Image` + assets~~ | Telltales, icons | done — `test_assets.py` |
| ~~P0~~ | ~~`font.pixelSize` tier map~~ | HUD typography | done — `fonts.tiers` |
| ~~P0~~ | ~~`opacity` / `visible` emit~~ | Blinkers, dimming | done — `instrument_cluster_static` |
| ~~P1~~ | ~~Theme tokens in QML~~ | Branding | done — `Theme.*` compile-time |
| ~~P1~~ | ~~`lv_scale` + tick labels~~ | Production gauges | done — `test_gauge_ticks.py` |
| ~~P1~~ | ~~`border.*` on `Rectangle`~~ | Cards, slots | done |
| ~~P2~~ | ~~Vehicle model / multi-setter API~~ | Live data without N setters | done — `vehicle-bind` |
| P2 | `NumberAnimation` subset | Polish | planned |
| P3 | `Row`/`Column` types (syntax sugar) | Ergonomics; anchors work today | planned |

---

## CI proof strategy

1. **Reject fixtures** — `tests/fixtures/qml/reject/manifest.yaml` (stable `DiagnosticCode`).
2. **Conformance manifest** — `examples/conformance/manifest.yaml` (`pass` / `partial` / `reject`).
3. **Feature proof tests** — e.g. `test_assets.py` for Image/opacity/fonts.
4. **Qt render parity** — `test_qt_parity_render.py` + `examples/conformance/qt_parity.yaml` (PyQt vs QVGL/SDL, tolerance per case).
5. **Per-example goldens** — IR + render under `examples/*/golden/`.
5. **Upstream sync** (optional CI job) — `examples/upstream/manifest.yaml` when Qt SDK present.

```bash
pytest tests/python/test_conformance_manifest.py tests/python/test_assets.py
pip install -e ".[qt-parity]" && pytest tests/python/test_qt_parity_render.py
qvglc check examples/mcu_minimal/minimal.qml
qvglc compile examples/icon_row/icon_row.qml -o /tmp/icon_gen
qvglc coverage path/to/upstream.qml   # quick tier probe
```

