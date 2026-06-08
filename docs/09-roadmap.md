# 9. Roadmap (planned iterations)

Forward-looking work only. Implemented capabilities: [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md), `pytest tests/python`.

## Current baseline

```text
QML (ultralite_v1) → parse/sema → IR → layout → emit LVGL C → qvgl_preview (PNG goldens)
```

Generic examples: minimal, gauge, bound label, static card, icons, ticks, animation, theme tokens.

**Explicitly not in-tree:** vehicle/CAN bindings, cluster profiles, automotive-specific emit paths. Upstream Qt vehicle demo QML is the **external** parity target once the generic compiler is ready.

---

## Next iterations

**Active plan (runtime data plane + C test suite):** [12-runtime-data-plane.md](12-runtime-data-plane.md) — Passo 1 bindings, Passo 2 dynamic plot, R1/R2 C proof.

### I1 — Layout ergonomics

`Row` / `Column` syntax sugar; full `horizontalAlignment` emit; anchor margin edge cases.

### I2 — Visual polish

`Image.PreserveAspectCrop`; Arc `rotation`; optional `Meter` → `lv_meter`.

### I3 — MCU delivery

**`esp32p4_qvgl_shell`** (ESP-IDF sibling project, not in `qvgl/`): compile UI on host, link runtime + BSP on P4. See [06-integration-shell.md](06-integration-shell.md).

### I4 — Bindings & expressions

**In progress as Passo 1** in [12-runtime-data-plane.md](12-runtime-data-plane.md): `property int` / `bool` / `string` setters + R2 C tests. Remaining: `ternary` / `map_linear` emit; broader string concat.

### I5 — Input & controls

`MouseArea` pressed/released; `lv_button` / `lv_imagebutton`; handler symbol table from QML.

### I6 — Typography

`font.weight` tiers; custom TTF embed; optional flat gradient.

### I7 — CI hardening

Split pytest vs render jobs; upstream sync job; IR negative fixtures; lexer/AST goldens.

### I8 — Upstream vehicle demo (validation only)

Compile Qt MCUs vehicle/cluster QML **without** adding domain code to QVGL:

- conformance tier `reference` + trim manifest
- high-tolerance render parity job (optional, out of default CI)
- gaps fed back as generic profile/emit work (I1–I6)

---

## Non-goals

- In-tree CAN / vehicle state / warning-lamp YAML
- Second profile for a specific display SKU
- `ListView` / `Repeater` / dynamic `Component` trees

---

## How to pick the next slice

1. [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md) — ❌ / ⚠️ rows.
2. `qvglc coverage file.qml` — designer report.
3. Committed example + pytest before marking ✅.
