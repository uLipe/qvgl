# Benchmarks and production notes

QVGL targets **static** cluster UIs: compile once, feed live data via generated setters or `qvgl_*_apply_vehicle()`.

## Host preview vs MCU

| Path | Use |
|------|-----|
| `qvglc run … --headless` | CI smoke, golden renders |
| `qvgl_preview --dump-fb` | PNG proof without SDL window |
| ESP-IDF shell (`esp32p4_qvgl_shell`) | On-device timing and PPA draw |

Preview runs on desktop SDL/dummy; MCU numbers depend on display bus, LVGL draw unit, and whether assets live in flash.

## Suggested MCU checks

1. **Cold boot** — `ui_*_create` + first `lv_timer_handler` after display init.
2. **Setter churn** — call `qvgl_*_set_*` or `apply_vehicle` at CAN rate (e.g. 20 Hz) and measure CPU %.
3. **Arc animation** — `NumberAnimation` maps to `lv_anim`; prefer short durations on MCUs or update needles directly from CAN without anim.
4. **Asset size** — `qvglc compile` reports embedded PNG/C arrays; keep telltales small (16–32 px).

## Animation policy

`NumberAnimation on value` is supported **only on `Arc`**. Other properties stay static; blinkers and telltales should use `visible`/`opacity` plus vehicle warning bits, not QML `Behavior`.

## CI reference

GitHub Actions runs `pytest tests/python` with LVGL checked out beside `qvgl/` (see `.github/workflows/ci.yml`). Render goldens use headless framebuffer dump; keep modules under test free of wall-clock SDL interaction.
