# QVGL examples

Generic reference UIs — each has `*.qml`, optional `golden/*.qvglir.json`, and optional `golden/frames/*.png`. All use `profiles/ultralite_v1.yaml`.

| Example | Notes |
|---------|-------|
| [mcu_minimal](mcu_minimal/) | Qt for MCUs minimal snapshot (primary upstream reference) |
| [turbo_gauge](turbo_gauge/) | bound `Arc` + `MouseArea` + label |
| [bound_label](bound_label/) | single `property real` → `Text` |
| [arc_animated](arc_animated/) | `NumberAnimation on value` → `lv_anim` |
| [gauge_ticks](gauge_ticks/) | `Arc` + `lv_scale` ticks |
| [icon_row](icon_row/) | embedded PNG `Image` row |
| [static_card](static_card/) | static layout + border |
| [themed_chip](themed_chip/) | `Theme.*` compile-time tokens |

```bash
qvglc run examples/<name>/<name>.qml
qvglc compile examples/<name>/<name>.qml -o /tmp/gen --lvgl-path ../lvgl
```

## Upstream Qt SDK

[upstream/](upstream/) — sync from Qt Creator via `tools/sync_upstream_examples.sh`. See [docs/08-upstream-examples.md](../docs/08-upstream-examples.md). Commercial automotive/cluster demos stay **reference-only** outside QVGL.

## Reject fixtures

[tests/fixtures/qml/reject/](../tests/fixtures/qml/reject/) — QML that must fail `qvglc check` with a stable code.
