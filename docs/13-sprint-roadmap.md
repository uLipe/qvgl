# 13. Sprint roadmap — Qt Quick Controls coverage

Living plan for incremental, deterministic coverage of the Ultralite/Controls subset. **Update status here when a phase lands.**

**Related:** [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md), [09-roadmap.md](09-roadmap.md), [12-runtime-data-plane.md](12-runtime-data-plane.md).

**Git:** commits on `main` only (no `feature/*` unless explicitly requested).

**MCU gate:** each new **control type** → example in `qvgl/examples/` + `esp32p4_qvgl_shell` `compile_ui.sh` + `idf.py build`.

---

## Goal

Coverage incremental and deterministic: manifest → sema → emit → R1/R2 → golden (where applicable).

---

## Phase status

| Phase | Focus | Status |
|-------|--------|--------|
| **1** | Responsividade (flex, `LinePlot` relayout) | ✅ Done; hybrid `Arc` responsive 🔮 optional |
| **2** | Infra conformidade (`manifest.yaml`, emit markers, `qvglc coverage`) | ✅ Mostly done |
| **3** | Material / Theme L1 | ✅ Done (`theme.py`, `material_card`, strict sema) |
| **4** | Controls backlog (types) | ⚠️ P0/P1 done; **P2 backlog** |
| **5** | Estados visuais e estilos | 🔄 **Active** |
| **6** | Runtime L2 + data plane | 📋 Planned |
| **7** | Shell MCU + display profiles | 📋 Planned |
| **8** | Paridade Ultralite (validação externa) | 📋 Planned |

---

## Phase 1 — Responsividade

- **Done:** flex root, layouts, `qvgl_plot_relayout`, `channel_plot_trim` / `line_plot_card` reference
- **Remaining:** hybrid emit responsive for `Arc` gauges (optional; fixed goldens at design resolution)

---

## Phase 2 — Infra de conformidade

- `examples/conformance/manifest.yaml` tiers (`smoke` / `pass` / `reference` / `reject`)
- `emit_markers.yaml` + `test_conformance_manifest.py`
- `qvglc coverage file.qml` as designer gate
- Trim checklist in [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md)

---

## Phase 3 — Material / Theme L1

- `Theme.*` / `Material.*` → `profiles/ultralite_v1.yaml` `theme.colors` + aliases
- Sema rejects unknown tokens
- Examples: `themed_chip`, `material_card`

---

## Phase 4 — Controls (por tipo)

Each type = profile + sema + IR + emit + L1 setter + example + pytest + emit markers.

| Pri | Type | LVGL | Status |
|-----|------|------|--------|
| P0 | `Slider` | `lv_slider` | ✅ `controls_inputs` |
| P0 | `Switch` / `CheckBox` | `lv_switch` / `lv_checkbox` | ✅ |
| P1 | `Button` | `lv_button` (filled) | ✅ |
| P1 | `ComboBox` | `lv_dropdown` | ✅ static `model: [...]` |
| P2 | `RadioButton` / `GroupBox` | composite | 📋 |
| P2 | `ProgressBar` | `lv_bar` | 📋 |
| — | `TextField` | — | ❌ out of scope (keyboard) |

**Phase 4 exit (P0/P1):** `controls_inputs` in manifest + P4 build.

**P2** is not blocking Phase 5.

---

## Phase 5 — Estados visuais e estilos (active)

- `enabled` / `opacity` / `visible` on all emitted control types (L1 `qvgl_widget_*`, bindings)
- Material-like chrome: accent track, radius, padding on Controls
- `pressed` / `released` handlers where profile allows (`LV_EVENT_PRESSED` / `RELEASED`)
- `LV_STATE_DISABLED` / `LV_STATE_CHECKED` via runtime setters
- Reject: `Behavior`, `State`, animations except `Arc.value` (already in sema)

**Exit:** `controls_styles` example + pytest emit markers + R2 `test_widget_enabled`.

---

## Phase 6 — Runtime L2

- `qvgl_controls.c` (optional consolidation; no duplicate L1)
- Plot: multi-series, legend
- R1/R2 per L2 module; CI split

---

## Phase 7 — Shell MCU

- `display.width/height` in profile or `compile_ui.sh` env
- `channel_plot_trim` / responsive reference on P4 full screen

---

## Phase 8 — Paridade Ultralite

- Manifest `reference` tier vs trimmed upstream QML
- `*_qt.qml` optional high-tolerance job
- Gaps → generic issues in phases 3–6 only

---

## Practical order (reference)

1. Phase 1 hybrid Arc (optional)
2. Phase 4 P0/P1 ✅ → **Phase 5** → Phase 4 P2 when needed
3. Phase 6–8 in parallel with product needs

**Do not** jump to Passo 3 MCU plot loop or upstream vehicle work while Controls sprint phases 4–5 are open unless the user explicitly pivots.
