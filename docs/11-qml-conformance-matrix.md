# 11. QML conformance matrix (Qt Creator → QVGL → LVGL)

Living compatibility reference for the **primary QVGL workflow**:

> *I want Qt for MCUs but can't pay for it — I design in **Qt Creator**, preview with desktop Qt, and use **QVGL** to compile the trimmed QML into **LVGL C** on my MCU.*

Planned work is tracked in [09-roadmap.md](09-roadmap.md).

**Not pixel-perfect Qt runtime parity** — QVGL is static compile-time codegen to LVGL. The matrix tracks *what you can keep from a Qt Creator QML* and *what you must trim or move to C*.

**Related:** [profiles/ultralite_v1.yaml](../profiles/ultralite_v1.yaml), [08-upstream-examples.md](08-upstream-examples.md), [07-proof-of-correctness.md](07-proof-of-correctness.md).

---

## Qt Creator workflow (practical guide)

### What you keep from a typical Qt Quick HMI

| You designed in Qt Creator… | QVGL today |
|-----------------------------|------------|
| Screen `Item` + fixed `width`/`height` | ✅ |
| `Rectangle` cards, borders, radius | ✅ |
| `Text` / **Controls `Label`** | ✅ (`Label` → `lv_label`) |
| `Image` icons (PNG) | ✅ embedded assets |
| `Arc` gauge + bound value label | ✅ hybrid emit + setters |
| `MouseArea` / **Controls `ToolButton`** tap | ✅ `app_on_*()` callbacks |
| **Layouts** `ColumnLayout` / `RowLayout` + `Layout.fill*` | ✅ flex pass after anchors |
| **Material** / **Theme** colors (`Material.foreground`, `Theme.accent`) | ✅ resolved at **compile time** from profile tokens |
| Module `property` + bindings (`value: speed`) | ✅ `real` + format strings on `Arc`/`Text` |
| Oscilloscope-style plot (not `Canvas`) | ✅ **`LinePlot`** + `PlotPoint` children → `lv_chart` |
| Anchor-based layout (`anchors.fill`, `centerIn`, margins) | ✅ |

### What you must trim or rewrite before `qvglc compile`

| Qt / Qt for MCUs habit | QVGL action |
|------------------------|-------------|
| `function foo() { … }` | ❌ Move logic to **C** (`qvgl_runtime`, `qvgl_plot`, app) |
| `Canvas` + `onPaint` | ❌ Use **`LinePlot`** or custom LVGL draw in app |
| `Connections`, `State`, `Behavior` | ❌ Wire updates via **module properties + setters** |
| `ListView`, `Repeater`, `Timer` | ❌ Static UI or app-driven refresh |
| C++ singletons (`VehicleStatus`, custom `Theme`) | ❌ `property` on root + app setters; `Theme.*` only as **profile colors** |
| `import` custom modules (`espFoC.theme`) | ❌ Map tokens into `ultralite_v1.yaml` `theme.colors` |
| `property var` / dynamic point arrays | ⚠️ static **`PlotPoint`** in QML; live data via C **`qvgl_plot_set_points`** |
| `font.weight`, custom TTF | ❌ Use Montserrat tiers (`font.pixelSize` → nearest tier) |
| `NumberAnimation` on arbitrary properties | ❌ Only **`NumberAnimation` on `Arc.value`** |
| Runtime Material theme switching | ❌ Colors baked at compile; restyle = recompile |
| `ScrollView`, `StackView`, popups, delegates | ❌ Not in profile |

### Recommended design loop

```text
Qt Creator / PyQt QML  →  qvglc check  →  trim until green
        ↓
qvglc compile  →  ui_*.c + preview PNG  →  pytest goldens / qt_parity
        ↓
ESP-IDF / bare-metal  →  link LVGL + generated UI + app setters
```

**Parity tests:** stock Qt Quick QML in `*_qt.qml` where needed (`line_plot_card_qt.qml`); QVGL QML uses declarative types (`LinePlot`). See [examples/conformance/qt_parity.yaml](../examples/conformance/qt_parity.yaml).

---

## How to read the matrix

Each feature is scored at four layers:

| Layer | Question |
|-------|----------|
| **Profile** | Allowed in `ultralite_v1.yaml`? |
| **Sema** | `qvglc check` accepts it? |
| **IR** | Lowered to IR bindings / properties? |
| **Emit** | Generates correct LVGL C? |

| Mark | Meaning |
|------|---------|
| ✅ | Works end-to-end (tests or committed example) |
| ⚠️ | Partial — known gaps |
| 📋 | Profile only — not fully emitted |
| ❌ | Rejected or out of scope |
| 🔮 | Planned — [09-roadmap.md](09-roadmap.md) |
| 🧱 | LVGL / hardware limit |

**Machine-checkable:** [examples/conformance/manifest.yaml](../examples/conformance/manifest.yaml).

---

## Imports

| Import | Profile | Sema | IR | Emit | Notes |
|--------|---------|------|-----|------|-------|
| `QtQuick` / `2.15` / `2.0` | ✅ | ✅ | ✅ | ✅ | Version optional (`import QtQuick`) |
| `QtQuick.Controls` | ✅ | ✅ | ✅ | ✅ | Subset: `Label`, `ToolButton` |
| `QtQuick.Layouts` | ✅ | ✅ | ✅ | ✅ | `ColumnLayout`, `RowLayout` |
| `QtQuick.Controls.Material` | ✅ | ✅ | ✅ | ✅ | `Material.*` → profile `theme.colors` at compile time |
| Custom / app modules | ❌ | ❌ | — | — | Map into profile or trim |
| `QtQuickUltralite.*` | ❌ | ❌ | — | — | Commercial; use QVGL types instead |
| `QtQuick.Shapes` | ❌ | ❌ | — | — | Use `Image` or `LinePlot` |

---

## Types

| QML type | Profile | Sema | IR | Emit → LVGL | Proof | Notes |
|----------|---------|------|-----|-------------|-------|-------|
| `Item` | ✅ | ✅ | ✅ | ✅ `lv_obj` | `mcu_minimal` | |
| `Rectangle` | ✅ | ✅ | ✅ | ✅ `lv_obj` | `static_card` | |
| `Text` | ✅ | ✅ | ✅ | ✅ `lv_label` | `static_card` | |
| `Label` (Controls) | ✅ | ✅ | ✅ | ✅ `lv_label` | `controls_card`, `line_plot_card` | Alias of `Text` in IR |
| `Arc` | ✅ | ✅ | ✅ | ✅ `lv_arc` (+ optional `lv_scale`) | `turbo_gauge`, `gauge_ticks` | |
| `Image` | ✅ | ✅ | ✅ | ✅ `lv_image` | `icon_row` | |
| `MouseArea` | ✅ | ✅ | ✅ | ✅ clickable `lv_obj` | `mcu_minimal` | `pressed`/`released` 📋 |
| `ToolButton` | ✅ | ✅ | ✅ | ✅ `lv_button` | `controls_card`, `line_plot_card` | `onClicked: app_on_*()` |
| `ColumnLayout` / `RowLayout` | ✅ | ✅ | ✅ | ✅ layout `lv_obj` | `controls_card`, `line_plot_card` | Flex after anchors |
| `LinePlot` | ✅ | ✅ | ✅ | ✅ `lv_chart` SCATTER | `line_plot_card`, `test_line_plot_card.py` | Not in desktop Qt — use `*_qt.qml` for parity |
| `PlotPoint` | ✅ | ✅ | ✅ | ✅ static series arrays | `line_plot_card` | Child of `LinePlot` only |
| `NumberAnimation` | ✅ | ✅ | ✅ | ✅ `lv_anim` | `arc_animated` | **`on value` inside `Arc` only** |
| `Meter` | ✅ | 📋 | ❌ | ❌ | — | Use `Arc` + ticks |
| `ListView` / `Repeater` / `Timer` | ❌ | ❌ | — | — | | |
| `Canvas` | ❌ | ❌ | — | — | | Use `LinePlot` |
| `State` / `Connections` / `Component` | ❌ | ❌ | — | — | | |

### Qt for MCUs Studio / commercial

| Studio / commercial | QVGL path |
|---------------------|-----------|
| `ArcItem` (dual arc) | `Arc` + ticks (`gauge_ticks`) |
| Studio `Gauge` | `turbo_gauge` reference |
| `Theme` singleton | `Theme.token` / `Material.*` → profile colors (compile time) |
| C++ context properties | Root `property` + generated setters |

---

## Properties (high-traffic)

| Property | Profile | Sema | IR | Emit | Proof | Notes |
|----------|---------|------|-----|------|-------|-------|
| `width` / `height` | ✅ | ✅ | ✅ | ✅ | `mcu_minimal` | |
| `implicitWidth` / `implicitHeight` | ✅ | ✅ | ✅ | ✅ | | Maps to `width`/`height` when unset |
| `required property` / `readonly property` | ✅ | ✅ | ✅ | ✅ | | Qt 6 modifiers; interface docs |
| `visible` / `opacity` / `enabled` | ✅ | ✅ | ✅ | ✅ | `widget_style.py` | |
| `color`, `radius`, `border.*` | ✅ | ✅ | ✅ | ✅ | `static_card` | |
| `text` literal / binding | ✅ | ✅ | ✅ | ✅ | `bound_label` | `format` / `sym` |
| `font.pixelSize` | ✅ | ✅ | ✅ | ✅ | `test_assets.py` | Tiers 14 / 36 / 48 |
| `font.weight` | ❌ | ❌ | — | — | | |
| `Layout.fillWidth` / `fillHeight` | ✅ | ✅ | ✅ | ✅ | `line_plot_card` | Attached props |
| `Layout.preferredWidth` / `preferredHeight` | ✅ | ✅ | ✅ | ✅ | | |
| `LinePlot` domain / grid / colors | ✅ | ✅ | ✅ | ✅ | `line_plot_card` | |
| `LinePlot.hoverEnabled` | ✅ | ✅ | ✅ | ✅ | `test_line_plot_card.py` | Crosshair + `cursorLabel` id |
| Arc gauge props | ✅ | ✅ | ✅ | ✅ | `turbo_gauge` | |
| `horizontalAlignment` | ✅ | ✅ | 📋 | ⚠️ | | Full emit 🔮 |

---

## Anchors & layout

| Feature | Profile | Sema | Layout | Emit | Notes |
|---------|---------|------|--------|------|-------|
| `anchors.fill` / `centerIn` / edges | ✅ | ✅ | ✅ | ✅ | |
| `anchors.margins` / `*Margin` | ✅ | ✅ | ⚠️ | ✅ | |
| `Layout.*` on children of `*Layout` | ✅ | ✅ | ✅ | ✅ | Flex resolver |
| `anchors.baseline` | ❌ | ❌ | — | — | |
| `GridLayout`, `StackLayout` | ❌ | ❌ | — | — | 🔮 |

---

## Module properties & expressions

| Feature | Profile | Sema | IR | Emit | Notes |
|---------|---------|------|-----|------|-------|
| `property real` + `sym` binding | ✅ | ✅ | ✅ | ✅ | Arc, Text setters |
| `property int` / `bool` / `string` / `color` | ✅ | ✅ | ✅ | ⚠️ | Parsed; full setter emit 🔮 |
| `property var` | ✅ | ⚠️ | ⚠️ | ❌ | Avoid in shipped QML |
| `toFixed(n) + "suffix"` | ✅ | ✅ | ✅ | ✅ | |
| `Math.*`, JS calls | ❌ | ❌ | — | — | |
| `function` declarations | ❌ | ❌ | — | — | Use C (`qvgl_plot`, app) |

---

## Signals & handlers

| Feature | Profile | Sema | IR | Emit | Notes |
|---------|---------|------|-----|------|-------|
| `MouseArea.onClicked` | ✅ | ✅ | ✅ | ✅ | |
| `ToolButton.onClicked` | ✅ | ✅ | ✅ | ✅ | |
| Handler `app_on_*()` | ✅ | ✅ | ✅ | ✅ | App implements C symbol |
| Arbitrary handler names | ❌ | ❌ | — | — | Must be `app_on_*` |
| `onPropertyChanged` | ❌ | ❌ | — | — | |

---

## Runtime C (layered — [12-runtime-data-plane.md](12-runtime-data-plane.md))

| Layer | Module | Role |
|-------|--------|------|
| L0 | `qvgl_runtime` | `qvgl_map_linear_f32`, init |
| L1 | `qvgl_widget` | Generic `lv_obj` text / visible / opa / arc |
| L2 | `qvgl_plot` | `LinePlot`: format, domain, points, cursor |
| L2 | `qvgl_arc` 🔮 | `Arc` value / ticks / anim helpers |
| L3 | `ui_*.c` emit | Create + thin setters → L1/L2 |

| API today | Layer | Proof |
|-----------|-------|-------|
| `qvgl_map_linear_f32` | L0 | `smoke.c` |
| `qvgl_plot_format_axis` | L0 | `smoke.c` |
| `qvgl_plot_compute_domain` | L0 | `smoke.c` |
| `qvgl_plot_set_points` / `set_domain` / `set_cursor` | L2 | `runtime_lvgl` test_plot |
| `qvgl_ui_*_set_plot_points` / `set_plot_domain` | L3→L2 | `line_plot_card` emit |
| `qvgl_ui_*_set_plot_cursor` | L3→L2 | `line_plot_card`, `--plot-cursor` |

---

## Examples map (what to copy)

| Example | Qt Creator lesson | Tier |
|---------|-------------------|------|
| `mcu_minimal` | Minimal green screen | ✅ pass |
| `static_card` | Card + anchors | ✅ pass |
| `bound_label` | `property` + binding | ✅ pass |
| `turbo_gauge` | Bound `Arc` | ✅ pass |
| `gauge_ticks` / `arc_animated` | Ticks + animation | ✅ pass |
| `icon_row` | PNG assets | ✅ pass |
| `themed_chip` | Theme tokens | ✅ pass |
| `controls_card` | Controls + Layouts chrome | ✅ (add to manifest) |
| `line_plot_card` | Full card + `LinePlot` | ✅ + **Qt parity** |

**Qt render parity** ([qt_parity.yaml](../examples/conformance/qt_parity.yaml)): `mcu_minimal`, `static_card`, `icon_row`, **`line_plot_card`** (QVGL vs `line_plot_card_qt.qml`).

---

## Remaining gaps (highest impact)

See [09-roadmap.md](09-roadmap.md). Summary:

| Area | Gap |
|------|-----|
| Plot | ✅ `qvgl_ui_*_set_plot_points` / `set_plot_domain` (L2); preview `--plot-animate` |
| Controls | `ScrollView`, `Button` styles, `StackView` |
| Layout | `GridLayout`, baseline anchors |
| Bindings | `int`/`bool`/`string` hybrid setters |
| Input | `MouseArea` pressed/released |
| Typography | `font.weight`, custom fonts |
| Image | `PreserveAspectCrop` |

---

## CI proof

```bash
qvglc check path/to/screen.qml
pytest tests/python/test_conformance_manifest.py
pytest tests/python/test_qt_parity_render.py   # pip install PyQt6
pytest tests/python/test_line_plot_card.py
```

Full suite: `.github/workflows/ci.yml` with LVGL at `../lvgl`.
