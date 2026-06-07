# 4. IR schema (v1)

## Design principles

- **Canonical form:** binary `.qvglir` (self-contained, no external schema runtime).
- **Debug interchange:** JSON dump with the same field IDs (`qvglc dump --json`).
- **Tree storage:** flat **node table** + child ranges (not recursive JSON on device).
- **Strings:** interned in a **string pool** (property names, ids, handler symbols).
- **Values:** typed **property blob** per node; bindings reference **expr records**.

Version magic: `QVGLIR_MAGIC = 'Q' 'V' 'G' '1'` (0x31564751 little-endian).

## File layout (binary)

```text
┌──────────────────┐
│ qvglir_header_t  │
├──────────────────┤
│ string pool      │
├──────────────────┤
│ node[]           │
├──────────────────┤
│ property[]       │  per-node slices via node.prop_off/count
├──────────────────┤
│ binding[]        │
├──────────────────┤
│ expr[]           │
├──────────────────┤
│ handler[]        │  signal → C symbol
├──────────────────┤
│ state[]          │  optional (PoC may omit)
├──────────────────┤
│ anim[]           │  optional (phase 2)
└──────────────────┘
```

All multi-byte integers **little-endian**. File must be parsed in one pass; offsets validated before use.

## Header

See `include/qvgl/ir_v1.h` — fields include:

| Field | Role |
|-------|------|
| `version` | `1` |
| `profile_hash` | FNV-1a of profile name (e.g. `ultralite_v1`) |
| `module_name` | string pool index (`turbo_gauge`) |
| `root_node` | index into `node[]` |
| section offsets/counts | strings, nodes, properties, bindings, exprs, handlers |

## Node

Each visual / logical object from QML becomes one node.

| Field | Type | Notes |
|-------|------|-------|
| `kind` | `qvgl_node_kind_t` | Item, Rectangle, Text, Arc, Meter, MouseArea, … |
| `name` | str index | optional QML `objectName` |
| `id` | str index | QML `id` (0 = none) |
| `parent` | u32 | parent index; `0xFFFFFFFF` = none (only root) |
| `child_first` | u32 | index into node[] |
| `child_count` | u16 | contiguous children |
| `prop_off` | u32 | slice into `property[]` |
| `prop_count` | u16 | |
| `flags` | u16 | `STATIC_LAYOUT`, `NEEDS_OBSERVER`, … |

Children are stored **depth-first** contiguously: a node's children occupy `[child_first, child_first + child_count)`.

## Property record

| Field | Type | Notes |
|-------|------|-------|
| `key` | str index | `width`, `color`, `text`, … |
| `value_kind` | enum | see below |
| `value` | union | inline or index |

### `value_kind` (v1)

| Kind | Payload |
|------|---------|
| `BOOL` | u8 |
| `I32` | i32 |
| `F32` | f32 |
| `COLOR` | u32 ARGB |
| `STRING` | str index |
| `ENUM` | u16 (e.g. anchor edge) |
| `BINDING` | index into `binding[]` |
| `RECT` | four f32 x,y,w,h |

Static QML literals use inline kinds. Dynamic QML properties use `BINDING`.

## Binding

Connects a **target** (node + property key) to an **expression**.

| Field | Type |
|-------|------|
| `target_node` | u32 |
| `target_key` | str index |
| `expr` | u32 → `expr[]` |
| `flags` | `ON_CHANGE`, `ONE_WAY`, … |

### Turbo gauge example (conceptual)

```text
binding[0]: target=label_node, key="text"
  expr=format("{pressure:.1f} bar", sym=pressure)

binding[1]: target=arc_node, key="value"
  expr=map_linear(sym=pressure, -0.7, 2.0, min_angle, max_angle)
```

Symbols refer to **module-level properties** declared in IR (`pressure` → slot in `qvgl_ui_state_t`).

## Expression (`expr[]`)

Small typed DAG stored flat (post-order indices).

| `expr_kind` | Arity | Meaning |
|-------------|-------|---------|
| `SYM` | 0 | module property or `id.prop` |
| `CONST_*` | 0 | literal |
| `ADD,SUB,MUL` | 2 | |
| `TERNARY` | 3 | |
| `MAP_LINEAR` | 5 | value, in_min, in_max, out_min, out_max |
| `FORMAT` | 2 | format string, inner expr |
| `CALL` | n | builtin only in v1 |

No arbitrary JS; unknown forms fail in **sema**, not at runtime.

## Handler

Maps QML `onClicked` etc. to a **C callback symbol** (app implements).

| Field | Type |
|-------|------|
| `node` | u32 |
| `signal` | str index (`clicked`, `pressed`, …) |
| `handler` | str index (`app_on_gauge_clicked`) |
| `flags` | `ASYNC` reserved |

## Module API (emitter output, not in IR file)

The emitter derives from IR:

```c
typedef struct {
    lv_obj_t *root;
    lv_obj_t *arc;
    lv_obj_t *label;
    float pressure;
} qvgl_ui_turbo_gauge_t;

void qvgl_ui_turbo_gauge_create(lv_obj_t *parent, qvgl_ui_turbo_gauge_t *ui);
void qvgl_ui_turbo_gauge_destroy(qvgl_ui_turbo_gauge_t *ui);
void qvgl_turbo_gauge_set_pressure(qvgl_ui_turbo_gauge_t *ui, float bar);
void qvgl_turbo_gauge_register_clicked(qvgl_ui_turbo_gauge_t *ui,
                                       void (*cb)(qvgl_ui_turbo_gauge_t *, void *),
                                       void *user_data);
```

IR stores which symbols and bindings justify these functions.

## JSON dump

Same semantics as binary; used for tests and review. Schema: [schema/qvglir-v1.schema.json](../schema/qvglir-v1.schema.json).

Example fragment:

```json
{
  "version": 1,
  "profile": "ultralite_v1",
  "module": "turbo_gauge",
  "root": 0,
  "nodes": [
    {
      "id": "root",
      "kind": "Item",
      "children": [1, 2, 3],
      "properties": { "width": 400, "height": 400 }
    }
  ],
  "module_properties": [
    { "name": "pressure", "type": "f32", "default": -0.7 }
  ],
  "bindings": [],
  "handlers": [
    { "node": "click_area", "signal": "clicked", "handler": "app_on_gauge_clicked" }
  ]
}
```

Binary is authoritative; JSON is generated by `dump`, not hand-edited long term (golden tests may use either once encoder exists).

## Validation rules

1. Single root; acyclic parent links.
2. `child_*` ranges do not overlap illegally.
3. All `str` indices in range.
4. `BINDING` expr types match property expected type (sema table per `kind` + key).
5. Profile whitelist: node `kind` and property keys allowed.
