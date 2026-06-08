# 6. MCU integration

## Boundary (generic vs platform)

QVGL stays **platform-agnostic**. No ESP-IDF, BSP, or flash scripts live in the QVGL tree.

```text
Host                          MCU (your project)
────                          ──────────────────
qvglc compile → generated/    ESP-IDF / CMake app
qvgl/runtime (L0–L2)    →     links runtime + generated ui_*.c
lvgl/                   →     board display port (BSP)
```

**Reference platform:** [`esp32p4_qvgl_shell`](../../esp32p4_qvgl_shell/) in the parent repo — ESP32-P4 EV board, `line_plot_card` sine feed, Passo 3 delivery loop.

## Host compile

```bash
qvglc compile qvgl/examples/line_plot_card/line_plot_card.qml \
  -o my_project/generated --lvgl-path ../lvgl
```

Outputs: `ui_<module>.c/h`, `qvgl_lv_conf.h`, `qvgl_lvgl.config`, `qvgl_sources.cmake`.

## Device loop (generic C)

```c
#include "lvgl.h"
#include "ui_line_plot_card.h"
#include "qvgl/qvgl_plot.h"

static qvgl_ui_line_plot_card_t ui;

void app_on_plot_close(void) { /* optional handler from QML */ }

void ui_init(void)
{
    qvgl_ui_line_plot_card_create(lv_screen_active(), &ui);
}

void ui_tick_plot(const qvgl_plot_point_t * pts, size_t n)
{
    qvgl_ui_line_plot_card_set_plot_points(&ui, pts, n);
}
```

Live updates: call generated `qvgl_ui_*_set_*()` or L2 `qvgl_plot_*` from timers/RTOS tasks. QVGL does not ship sensors, CAN, or vehicle logic.

## CMake (any toolchain)

Optional helper for non-IDF builds:

```cmake
set(QVGL_ROOT /path/to/qvgl)
set(QVGL_LVGL_PATH /path/to/lvgl)
set(QVGL_LV_CONF_DIR ${QVGL_ROOT}/tests/preview)  # host lv_conf.h
include(${QVGL_ROOT}/cmake/qvgl_runtime.cmake)
qvgl_add_runtime_libraries()
target_link_libraries(my_app PRIVATE qvgl_runtime_lvgl lvgl ${QVGL_GENERATED}/ui_foo.c)
```

ESP-IDF projects typically use a local component (see `esp32p4_qvgl_shell/components/qvgl_app`) instead of this file.

## LVGL config

- **ESP-IDF:** merge `generated/qvgl_lvgl.config` into `sdkconfig.defaults`; keep `CONFIG_LV_CONF_SKIP=y`.
- **Host / custom:** `#include "generated/qvgl_lv_conf.h"` or `rsource` the emitted Kconfig fragment.

## Passo 3 checklist

- [ ] `qvglc compile` in CI or `scripts/compile_ui.sh` on dev machine
- [ ] Firmware links `qvgl/runtime` + `generated/ui_*.c` + LVGL
- [ ] Display init in **platform** project only
- [ ] App task/timer ≥10 Hz calling setters (plot, gauge, bindings)
