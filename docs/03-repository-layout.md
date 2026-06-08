# 3. Repository layout

## Tree

```text
qvgl/
├── profiles/ultralite_v1.yaml    # single QML subset
├── examples/                     # generic reference UIs
│   ├── mcu_minimal/
│   ├── turbo_gauge/
│   ├── conformance/manifest.yaml
│   └── upstream/manifest.yaml
├── qvglc/
│   ├── cli.py
│   ├── parser/
│   ├── ir/
│   ├── layout/
│   ├── emit_lvgl/
│   └── run_preview.py
├── runtime/qvgl_runtime.c
└── tests/
    ├── python/                   # pytest (CI)
    └── preview/                  # qvgl_preview
```

## CLI

```text
qvglc check | coverage | compile | run | emit | ir | dump | validate | preview
```

All commands default to `profiles/ultralite_v1.yaml` unless `--profile` is passed (only one profile ships today).

## Generated bundle (`qvglc compile -o OUT`)

```text
ui_<module>.c / .h
qvgl_<module>.h              # when module has bound properties
qvgl_<module>_assets.*       # when Image nodes present
qvgl_preview_shim.c/h
qvgl_lv_conf.h, qvgl_lvgl.config, qvgl_sources.cmake
```

`examples/*/golden/generated/` is gitignored.

## Siblings

```text
esp-idf-exps/lvgl/              # --lvgl-path
esp32p4_lvgl_benchmark/         # LVGL on P4 reference
```
