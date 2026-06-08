# Benchmarks and production notes

QVGL targets **static** UIs: compile once, update via generated `qvgl_<module>_set_*()` from application code.

## Host vs MCU

| Path | Use |
|------|-----|
| `qvglc run --headless` | CI smoke, PNG goldens |
| `qvgl_preview --dump-fb` | framebuffer capture |
| IDF + `generated/` | on-device timing |

## MCU checks

1. Cold boot — `ui_*_create` + first `lv_timer_handler`.
2. Setter rate — call setters at your data rate; measure CPU.
3. Arc animation — `lv_anim` cost; prefer direct setter on tight MCUs.
4. Asset size — embedded PNG/C size in compile output.

## Animation policy

`NumberAnimation on value` only on `Arc`. Other properties: static QML or C-side updates.

## CI

`.github/workflows/ci.yml` — full `pytest tests/python`, LVGL at `../lvgl`, `SDL_VIDEODRIVER=dummy`.
