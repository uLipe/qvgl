# Trim checklist — Qt Creator / Qt for MCUs → QVGL

One-page workflow for designers. Full matrix: [11-qml-conformance-matrix.md](11-qml-conformance-matrix.md).

## 1. Before you design

- Target profile: [ultralite_v1.yaml](../profiles/ultralite_v1.yaml)
- MCU resolution: [esp32p4_1024x600.yaml](../profiles/esp32p4_1024x600.yaml) + `--mcu-root` on compile
- Logic lives in **C** (`app_on_*`, `qvgl_*_set_*`); QML is layout + bindings only

## 2. Imports (keep)

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
```

Remove: custom modules, `QtQuickUltralite`, `QtQuick.Shapes`, `QtQuick.Controls` extras (`ScrollView`, …).

## 3. Replace / remove

| Remove | Use instead |
|--------|-------------|
| `function foo()` | C handler `app_on_foo()` |
| `Canvas` / `onPaint` | `LinePlot` + `PlotPoint` |
| `ListView` / `Repeater` / `Timer` | Static tree or app refresh |
| `State` / `Behavior` / `Connections` | Module `property` + setters |
| `ArcItem` / Studio `Gauge` | Single `Arc` (`turbo_gauge` pattern) |
| `property var` / dynamic arrays | Static `PlotPoint` children; live data in C |
| `Theme` singleton / C++ context | Root `property` + `Material.*` / profile colors |
| `font.weight` | `font.pixelSize` only (Montserrat tiers) |

## 4. Handlers

Only:

```qml
onClicked: app_on_something()
onMoved: app_on_gain_moved()
onValueChanged: app_on_gain_changed()
```

Implement `void app_on_something(void)` in `app_main.c`.

## 5. Validate

```bash
qvglc check my_screen.qml
qvglc coverage my_screen.qml    # human-readable gap report
qvglc compile my_screen.qml -o generated/ --lvgl-path ../lvgl
```

## 6. Deploy (ESP32-P4 reference)

```bash
cd esp32p4_qvgl_shell
QVGL_QML=../qvgl/examples/my_screen/my_screen.qml \
QVGL_MODULE=my_screen \
./scripts/compile_ui.sh
idf.py -DQVGL_UI_MODULE=my_screen build flash
```

## 7. When it still fails

1. Read `qvglc coverage` output — maps to matrix ❌ rows
2. Compare with closest example in [examples/README.md](../examples/README.md)
3. For plots: copy `channel_plot_trim` or `line_plot_card`
4. For gauges: copy `turbo_gauge`, not upstream `Gauge.qml`
