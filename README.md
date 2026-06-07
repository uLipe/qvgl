# QVGL

Static QML-to-LVGL compiler for embedded targets. Design in Qt Creator with Qt Quick / Qt for MCUs examples; deploy generated C + LVGL — **no Qt runtime on device**.

## Getting started

Requires [LVGL](https://github.com/lvgl/lvgl) at `../lvgl` and Python 3.10+.

```bash
pip install -e ".[test]"
qvglc run examples/mcu_minimal/minimal.qml
```

Same QML shape as Qt Creator’s Qt for MCUs **minimal** example.

Bound properties (`property real` + Arc / Text bindings):

```bash
qvglc run examples/cluster_dual_gauge/cluster_dual_gauge.qml \
  --profile profiles/cluster_480x272.yaml \
  --set speed_kmh=120 --set rpm=3500
```

Vehicle struct → UI (CAN / app data):

```bash
qvglc compile examples/cluster_dual_gauge/cluster_dual_gauge.qml -o /tmp/gen \
  --profile profiles/cluster_480x272.yaml
qvglc vehicle-bind examples/cluster_dual_gauge/vehicle_bindings.yaml -o /tmp/gen
```

Static cluster frame (480×272):

```bash
qvglc run examples/cluster_shell/cluster_shell.qml --profile profiles/cluster_480x272.yaml
```

Headless smoke:

```bash
qvglc run examples/mcu_minimal/minimal.qml --headless --exit --loop-frames 30
```

Compiler output goes to `-o` / `build/run/<module>/` — not committed; only QML, IR goldens, and render PNG fixtures live in `examples/`.

## Documentation

Start with [docs/README.md](docs/README.md).

## Layout

```text
qvgl/
  docs/           architecture, IR, testing
  profiles/       supported QML subset
  examples/       reference UIs + conformance manifest
  qvglc/          host compiler (Python)
  runtime/        on-device glue (C)
  tests/          pytest + SDL preview harness
```

## Toolchain

```bash
pytest tests/python
pip install -e ".[qt-parity]"   # optional: PyQt6 render parity
pytest tests/python/test_qt_parity_render.py
qvglc check examples/mcu_minimal/minimal.qml
qvglc compile examples/turbo_gauge/turbo_gauge.qml -o /tmp/gen
```

## MCU integration

Copy `qvglc compile` output into your IDF project (e.g. `esp32p4_qvgl_shell/generated/`).
