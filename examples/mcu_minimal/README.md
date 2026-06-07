# Qt for MCUs — minimal (getting started)

Committed snapshot of the official Qt for MCUs `examples/minimal/minimal.qml`. This is the **Ultralite-compatible** reference screen: green `Rectangle` + centered `Text`.

| Stage | Artifact |
|-------|----------|
| QML | `minimal.qml` (SHA256 in `UPSTREAM.sha256`) |
| IR | `golden/minimal.qvglir.json` |
| Emit | `golden/generated/ui_minimal.c` |
| Render | `golden/frames/minimal.png` |

```bash
qvglc run examples/mcu_minimal/minimal.qml
```
