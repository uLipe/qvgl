# 4. IR schema (v1)

## Design principles

- **Canonical form:** binary `.qvglir` (self-contained).
- **Debug interchange:** JSON dump (`qvglc dump --json`, committed `examples/*/golden/*.qvglir.json`).
- **Tree storage:** flat **node table** + parent/child indices.
- **Strings:** interned pool (ids, handler symbols, property keys).
- **Values:** typed properties per node; bindings reference **expr** records.

Version magic: `QVGLIR_MAGIC = 'Q' 'V' 'G' '1'`.

## File layout (binary)

```text
┌──────────────────┐
│ qvglir_header_t  │
├──────────────────┤
│ string pool      │
├──────────────────┤
│ node[]           │
├──────────────────┤
│ property[]       │
├──────────────────┤
│ binding[]        │
├──────────────────┤
│ expr[]           │
├──────────────────┤
│ handler[]        │
├──────────────────┤
│ state[]          │  reserved
├──────────────────┤
│ anim[]           │  reserved (unused — see below)
└──────────────────┘
```

Little-endian throughout. Offsets validated on load (`qvglc/ir/validate.py`).

## Header

See `include/qvgl/ir_v1.h`:

| Field | Role |
|-------|------|
| `version` | `1` |
| `profile_hash` | FNV-1a of profile name |
| `module_name` | string pool index |
| `root_node` | index into `node[]` |
| section offsets/counts | strings, nodes, properties, bindings, exprs, handlers |

## Node

| Field | Notes |
|-------|-------|
| `kind` | Item, Rectangle, Text, Arc, Image, MouseArea, … |
| `id` | QML `id` (optional) |
| `parent` / children | tree via indices |
| `properties` | literals, anchors dict, binding refs |

### QML lowering notes

| QML construct | IR representation |
|---------------|-------------------|
| `property real foo` | `module_properties[]` + binding exprs |
| `NumberAnimation on value` (Arc) | `valueAnimationDuration` int on arc node — **not** a child node or `anim[]` record |
| `Theme.primary` | resolved color literal at build time |
| `anchors.*` | `properties.anchors` map for layout pass |

## Property values

| Kind | Use |
|------|-----|
| literals | bool, i32, f32, color, string |
| `binding` | `{ "binding": { "sym": "pressure" } }` or `format` expr |
| `anchors` | nested map consumed by `qvglc/layout` |

## Binding & expressions

Bindings connect `(node, key)` → expr DAG:

| `expr` op | Support |
|-----------|---------|
| `sym` | module property |
| `const` | numeric / string |
| `format` | `toFixed(n) + suffix` lowered in ir_builder |
| `add` | only format-add pattern |
| `map_linear`, `ternary` | in profile; emit partial — see roadmap |

Unknown ops fail in **sema**, not at runtime.

## Handlers

`MouseArea.onClicked: app_on_gauge_clicked()` → handler record with C symbol name (app implements).

## Module API (emitter output, not stored in `.qvglir`)

Hybrid modules derive:

```c
typedef struct {
    lv_obj_t * root;
    lv_obj_t * gauge_arc;
    float pressure;
} qvgl_ui_turbo_gauge_t;

void qvgl_ui_turbo_gauge_create(lv_obj_t * parent, qvgl_ui_turbo_gauge_t * ui);
void qvgl_turbo_gauge_set_pressure(qvgl_ui_turbo_gauge_t * ui, float bar);
```

Static modules expose only `ui_*_create` (no `qvgl_<module>.h`).

## JSON dump

Same semantics as binary; used for goldens and review. Schema: [schema/qvglir-v1.schema.json](../schema/qvglir-v1.schema.json).

## Validation rules

1. Single root; acyclic parents.
2. String indices in range.
3. Profile whitelist for node kinds and property keys.
4. Binding types compatible with target property (sema).
