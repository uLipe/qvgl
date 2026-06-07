# 6. MCU integration shell

## Strategy

QVGL v1 does **not** embed into ESP-IDF as a component. The compiler runs on the host; the MCU project only consumes **`generated/`**.

## `esp32p4_qvgl_shell` (planned sibling)

Duplicate of `esp32p4_lvgl_benchmark` with:

- Same BSP, display, PPA/LVGL `sdkconfig.defaults` baseline
- **No** LVGL demos (`CONFIG_LV_USE_DEMO_*` off)
- Minimal `main.c`:

```c
#include "lvgl.h"
#include "generated/ui_turbo_gauge.h"

void app_main(void)
{
    /* display init — same as benchmark */
    qvgl_ui_turbo_gauge_t ui;
    qvgl_ui_turbo_gauge_create(lv_screen_active(), &ui);
    qvgl_turbo_gauge_set_pressure(&ui, 0.0f);

    for (;;) {
        lv_timer_handler();
    }
}
```

## Workflow

```bash
# host
qvglc compile qvgl/examples/turbo_gauge/turbo_gauge.qml \
  -o esp32p4_qvgl_shell/generated \
  --lvgl-path lvgl \
  --profile ultralite_v1

# device
cd esp32p4_qvgl_shell && idf.py build flash
```

## Merging LVGL config

1. Add to project `Kconfig.projbuild`:

   ```kconfig
   rsource "generated/qvgl_lvgl.config"
   ```

2. Or `#include "generated/qvgl_lv_conf.h"` from `lv_conf.h` / project override header.

QVGL fragments only **enable required options**; user `sdkconfig` remains authoritative.

## `--lvgl-path` capability check

Before emit, probe detects e.g.:

- LVGL major/minor from `lv_version.h`
- Whether `lv_meter`, `lv_arc`, fonts, `LV_USE_FLOAT` exist

Mismatch → compile error with fix hint (`enable CONFIG_LV_USE_METER` or upgrade LVGL).

## Git hygiene

- `esp32p4_qvgl_shell/generated/` → **gitignored**
- Golden outputs live under `qvgl/examples/.../golden/` for tests only
