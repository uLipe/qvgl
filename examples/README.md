# QVGL examples

Each example has `*.qml`, optional `golden/*.qvglir.json` (IR fixture), and `golden/frames/*.png` (render fixture). Run `qvglc compile … -o /tmp/gen` for LVGL C output.

| Example | Notes |
|---------|-------|
| [mcu_minimal](mcu_minimal/) | Qt for MCUs minimal snapshot |
| [turbo_gauge](turbo_gauge/) | single Arc + binding |
| [gauge_ticks](gauge_ticks/) | Arc + `lv_scale` ticks |
| [cluster_dual_gauge](cluster_dual_gauge/) | dual Arc + `vehicle_bindings.yaml` |
| [cluster_shell](cluster_shell/) | static 480×272 frame |
| [instrument_cluster_static](instrument_cluster_static/) | trimmed cluster HUD |
| [icon_row](icon_row/) | PNG telltales |
| [static_card](static_card/) | static layout card |
| [themed_chip](themed_chip/) | `Theme.*` tokens |

## Upstream Qt SDK

[upstream/](upstream/) — sync from Qt Creator via `tools/sync_upstream_examples.sh`. See [docs/08-upstream-examples.md](../docs/08-upstream-examples.md).

## Reject fixtures

[tests/fixtures/qml/reject/](../tests/fixtures/qml/reject/) — QML that must fail `qvglc check` with a stable code.
