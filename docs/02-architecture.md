# 2. Architecture

## End-to-end flow

```text
┌─────────────┐     ┌──────────┐     ┌─────────┐     ┌──────────────┐
│  .qml file  │────▶│  Front   │────▶│ Middle  │────▶│   Backend    │
│ (Qt Creator)│     │ parse +  │     │ layout +│     │ emit LVGL    │
│             │     │ sema     │     │ bind    │     │ + conf frag  │
└─────────────┘     └────┬─────┘     └────┬────┘     └──────┬───────┘
                         │                │                  │
                         ▼                ▼                  ▼
                    Document AST    qvglir (binary)    ui.c / ui.h
                                    [optional .json]    qvgl_lv_conf.h
                                                        qvgl_runtime (link)
```

## Stages

### Front (`lib/parser`, `lib/sema`)

- Lex/parse QML object tree for the active **profile**.
- Resolve `id`, types, allowed properties.
- Lower to **IR v1** (canonical binary tree).
- Reject unsupported constructs with profile-aware diagnostics.

### Middle (`lib/layout`, `lib/bind`)

- Resolve **anchors subset** and implicit size where possible at compile time.
- Build **binding graph** (which IR properties depend on which symbols).
- Mark nodes that need **runtime observers** vs fully static init.

### Backend (`lib/emit_lvgl`, `lib/lvgl_probe`)

- Input: IR + `--lvgl-path` capability table.
- Output:
  - `ui_<name>.c` / `ui_<name>.h` — `lv_obj` tree, `lv_style_t`, create API
  - `qvgl_<name>.h` — public setters / getters for bound properties
  - `qvgl_lv_conf.h` / `qvgl_lvgl.config` — minimum LVGL options
  - `qvgl_sources.cmake` — list of generated sources for the app

### Runtime (`runtime/qvgl_runtime.c`)

- Shared math/helpers only when **≥2 modules** need the same logic.
- Per-screen bindings, setters, and click handlers live in **generated `ui_*.c`** (self-contained).
- Preview and MCU shell link runtime only when a helper is actually used.

## Profile

YAML file (`profiles/ultralite_v1.yaml`) defines allowed types, properties, binding forms, and coverage rules. The CLI loads it for `validate` and `coverage`.

## LVGL as backend (v1)

IR nodes carry **visual intent** (geometry, colors, fonts). The emitter maps to `lv_obj` + `lv_style_t`. Future backends (e.g. direct PPA scene) would consume the same IR without changing the front-end.

## Self-contained rule

No link-time dependency on Qt. Reference implementations may be studied offline; all shipped code lives under `qvgl/`.
