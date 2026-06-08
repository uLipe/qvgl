# QVGL

Static QML-to-LVGL compiler. Design in Qt Creator with Qt Quick / Qt for MCUs examples; deploy generated C + LVGL — **no Qt runtime on device**.

QVGL is **generic**: one profile (`ultralite_v1`), QML in → LVGL UI out, validated with pytest and a headless SDL preview harness.

## Getting started

Requires [LVGL](https://github.com/lvgl/lvgl) at `../lvgl` and Python 3.10+.

```bash
pip install -e ".[test]"
qvglc run examples/mcu_minimal/minimal.qml
```

Qt for MCUs **minimal** reference (upstream-aligned):

```bash
qvglc run examples/mcu_minimal/minimal.qml
```

Bound property + gauge:

```bash
qvglc run examples/turbo_gauge/turbo_gauge.qml --set pressure=1.2
```

Compile to a directory:

```bash
qvglc compile examples/turbo_gauge/turbo_gauge.qml -o /tmp/gen --lvgl-path ../lvgl
```

Headless smoke:

```bash
qvglc run examples/mcu_minimal/minimal.qml --headless --exit --loop-frames 30
```

Compiler output goes to `-o` / `build/run/<module>/` — not committed; examples keep QML + IR/PNG goldens only.

## Documentation

Start with [docs/README.md](docs/README.md). Planned work: [docs/09-roadmap.md](docs/09-roadmap.md).

**Out of scope in-tree:** automotive/vehicle demos, CAN bindings, and Qt cluster-specific tooling live outside this repo. The long-term goal is to compile upstream Qt MCUs vehicle QML with the same generic pipeline — without baking that domain into QVGL itself.

## Layout

```text
qvgl/
  docs/           architecture, IR, testing
  profiles/       ultralite_v1.yaml (single supported subset)
  examples/       generic reference UIs
  qvglc/          host compiler (Python)
  runtime/        minimal on-device glue (C)
  tests/          pytest + SDL preview harness
```

## Toolchain

```bash
pytest tests/python
qvglc check examples/mcu_minimal/minimal.qml
qvglc compile examples/turbo_gauge/turbo_gauge.qml -o /tmp/gen
```

Optional Qt render parity: `pip install -e ".[qt-parity]"` then `pytest tests/python/test_qt_parity_render.py`.

## MCU integration

Copy `qvglc compile` output into your IDF project. See [docs/06-integration-shell.md](docs/06-integration-shell.md).
