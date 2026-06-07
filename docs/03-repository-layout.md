# 3. Repository layout

## Tree (v1 sketch)

```text
qvgl/
├── README.md
├── CMakeLists.txt                 # host: qvglc, tests, preview
├── docs/                          # top-down docs (this folder)
├── schema/
│   └── qvglir-v1.schema.json      # JSON mirror of IR (debug interchange)
├── include/
│   └── qvgl/
│       ├── ir_v1.h                # binary IR C layout + enums
│       └── qvgl_runtime.h         # public runtime API (hand-written)
├── profiles/
│   └── ultralite_v1.yaml          # QML subset + coverage rules
├── examples/
│   └── turbo_gauge/
│       ├── turbo_gauge.qml        # design in Qt Creator
│       ├── README.md              # how to open / export reference
│       └── golden/
│           ├── turbo_gauge.qvglir   # committed binary IR
│           ├── turbo_gauge.qvglir.json
│           ├── generated/           # gitignored — qvglc compile output
│           └── frames/              # render PNG goldens (committed fixtures)
├── qvglc/                         # Python package (host compiler)
│   ├── cli.py
│   └── ir/
├── pyproject.toml
├── runtime/
│   ├── qvgl_runtime.c
│   └── CMakeLists.txt
└── tests/
    ├── CMakeLists.txt
    ├── harness/
    │   └── qvgl_test.h            # minimal test macros (no external framework)
    ├── python/
    │   └── test_ir_roundtrip.py
    ├── unit/
    │   ├── test_lexer.c           # planned
    │   └── test_parser.c
    ├── integration/
    │   └── test_turbo_gauge_emit.c
    ├── preview/
    │   ├── main_sdl.c             # LVGL + SDL, ARGB8888 → RGB565 blit
    │   └── CMakeLists.txt
    └── fixtures/
        └── lvgl_stub/             # minimal headers for emit-only compile tests
```

## Sibling projects (outside `qvgl/`)

```text
esp-idf-exps/
├── lvgl/                          # --lvgl-path target
├── esp32p4_lvgl_benchmark/        # untouched reference
└── esp32p4_qvgl_shell/            # blank copy: BSP + LVGL, empty UI (planned)
    ├── main/
    │   └── main.c                 # init display + #include generated/ui_*.h
    └── generated/                 # gitignored; filled by qvglc
        └── .gitkeep
```

## Build (host)

**Compiler (Python):**

```bash
pip install -e .
pytest tests/python
qvglc ir examples/turbo_gauge/golden/turbo_gauge.qvglir.json -o /tmp/out.qvglir
```

**Runtime + preview (CMake):**

| Target | Purpose |
|--------|---------|
| `qvgl_runtime` | static lib for preview + device |
| `qvgl_tests` | C runtime smoke |
| `qvgl_preview` | SDL app (planned) |

```bash
cmake -B build -DQVGL_LVGL_PATH=/path/to/lvgl
cmake --build build && ctest --test-dir build
```

## CLI commands (planned)

```text
qvglc compile  <file.qml> -o <outdir> --profile ultralite_v1 --lvgl-path <lvgl>
qvglc validate <file.qml> --profile ultralite_v1
qvglc ir       <file.qml> -o <file.qvglir>
qvglc emit     <file.qvglir> -o <outdir> --lvgl-path <lvgl>
qvglc dump     <file.qvglir> [--json]
qvglc coverage <file.qml> --profile ultralite_v1
qvglc preview  <outdir>              # run SDL harness on generated UI
```

## Generated artifact bundle

Each `compile` writes:

```text
<outdir>/
  ui_<module>.c
  ui_<module>.h
  qvgl_<module>.h          # app-facing API (setters, handler registration)
  qvgl_lv_conf.h
  qvgl_lvgl.config
  qvgl_sources.cmake
```
