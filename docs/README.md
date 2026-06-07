# QVGL documentation

Read in order (top-down).

| # | Document | What you learn |
|---|----------|----------------|
| 1 | [01-overview.md](01-overview.md) | Goals, non-goals, Qt Creator workflow |
| 2 | [02-architecture.md](02-architecture.md) | Pipeline stages, profiles, LVGL backend |
| 3 | [03-repository-layout.md](03-repository-layout.md) | Directory tree, build targets, CLI |
| 4 | [04-ir-schema.md](04-ir-schema.md) | IR v1 binary layout, node model, bindings |
| 5 | [05-testing-and-preview.md](05-testing-and-preview.md) | Unit / integration / SDL preview |
| 6 | [06-integration-shell.md](06-integration-shell.md) | `esp32p4_qvgl_shell`, generated artifacts |
| 7 | [07-proof-of-correctness.md](07-proof-of-correctness.md) | Golden strategy: IR, parser, render E2E |
| 8 | [08-upstream-examples.md](08-upstream-examples.md) | Real Qt Creator / SDK example sources |
| 11 | [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md) | Qt Quick / Ultralite ↔ QVGL ↔ LVGL compatibility |
| — | [benchmarks.md](benchmarks.md) | MCU timing notes, animation policy, CI reference |

## Related files

- [schema/qvglir-v1.schema.json](../schema/qvglir-v1.schema.json) — JSON dump schema (debug interchange)
- [include/qvgl/ir_v1.h](../include/qvgl/ir_v1.h) — C types for binary IR v1
- [profiles/ultralite_v1.yaml](../profiles/ultralite_v1.yaml) — first supported QML subset
