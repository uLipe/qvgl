# 2. Architecture

## End-to-end flow

```text
┌─────────────┐     ┌──────────────┐     ┌─────────┐     ┌────────────────────┐
│  .qml file  │────▶│ qvglc/parser │────▶│ layout  │────▶│ qvglc/emit_lvgl    │
│             │     │ lex parse    │     │ anchors │     │ static | hybrid UI │
│             │     │ sema IR build│     │         │     │ assets preview shim│
└─────────────┘     └──────┬───────┘     └────┬────┘     └─────────┬──────────┘
                           │                  │                    │
                           ▼                  ▼                    ▼
                      Module (IR)        NodeLayout[]         ui_*.c/h
                      .qvglir binary                          qvgl_*.h (if bound)
```

## Stages

### Front (`qvglc/parser`)

Lexer, parser, sema against **`ultralite_v1`**, IR builder. Rejects unsupported QML with stable `DiagnosticCode`.

Special lowering: `NumberAnimation on value` (Arc only) → `valueAnimationDuration`; `Theme.*` → compile-time colors.

### Middle (`qvglc/layout`)

Compile-time anchor resolver → `Rect` per node.

### Backend (`qvglc/emit_lvgl`)

| Mode | When | Output |
|------|------|--------|
| **Static** | no module properties | literals baked in `ui_*.c` |
| **Hybrid** | `property` bindings and/or `Arc` | `qvgl_<module>_set_*()` + preview shim |

Widgets: `Rectangle`, `Text`, `Arc` (+ optional `lv_scale` ticks), `Image`, `MouseArea`, `Item`.

### Runtime (layered — see [12-runtime-data-plane.md](12-runtime-data-plane.md))

```text
L0 qvgl_runtime   → math, init (no lv_obj)
L1 qvgl_widget  → generic label/visible/opa/arc ops
L2 qvgl_plot, qvgl_arc, … → one module per dynamic QML type
L3 ui_*.c       → create + thin setters calling L1/L2
```

Generated setters must not duplicate LVGL mutation logic; new Ultralite/Controls dynamics extend L2 (or L1 for simple property keys).

## Profile

Single file: `profiles/ultralite_v1.yaml` — types, properties, anchors, binding exprs, font tiers, theme color tokens, animations.

## LVGL backend

IR carries visual intent; emitter targets LVGL 9 `lv_obj` + styles. Probed via `--lvgl-path`.

## Self-contained rule

No link-time dependency on Qt.
