# Turbo pressure gauge (PoC)

Reference UI for QVGL v1:

- Range: **−0.7 … 2.0 bar**
- `onClicked` → app handler `app_on_gauge_clicked`
- App sets value via `qvgl_turbo_gauge_set_pressure()`

## Qt Creator

1. Open `turbo_gauge.qml` as a Qt Quick project (or paste into a `.ui.qml` file).
2. Use as **visual reference** for SDL preview comparison.
3. Stay within `profiles/ultralite_v1.yaml`.

## Golden artifacts

- `golden/turbo_gauge.qvglir.json` — hand-written IR dump (until encoder exists)
- `golden/emit/` — expected generated C snippets (integration tests)
