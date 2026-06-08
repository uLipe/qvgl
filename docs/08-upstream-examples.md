# 8. Upstream Qt examples (source of truth)

QVGL examples and negative fixtures should come from **real Qt-shipped QML**, not hand-written approximations. Qt Creator’s **Welcome → Examples** browser is just a UI over files already on disk from the Qt SDK / Maintenance Tool.

**Related:** [07-proof-of-correctness.md](07-proof-of-correctness.md), [profiles/ultralite_v1.yaml](../profiles/ultralite_v1.yaml).

---

## Where examples live

| Source | Typical path (this machine) | What Qt Creator shows |
|--------|----------------------------|------------------------|
| **Qt 6 Quick** | `$QT_EXAMPLES/quick/` e.g. `~/Qt/Examples/Qt-6.11.1/quick/` | Examples for Desktop Qt Quick kit |
| **Qt for MCUs** | `$QTMCU/examples/` e.g. `~/Qt/QtMCUs/2.12.1/examples/` | Ultralite / embedded demos (gauge, cluster) |
| **Git (optional)** | `https://code.qt.io/qt/qtdeclarative.git` tag `v6.11.1` → `examples/quick/` | Same files as SDK when examples module installed |

There is **no separate “Qt Creator examples download”** — install components via **Qt Maintenance Tool** (Qt 6.x → Qt Quick examples; Qt for MCUs → SDK + examples).

---

## Tiers for QVGL

| Tier | Purpose | Upstream examples |
|------|---------|-------------------|
| **pass** | Must parse + sema + IR/render goldens where committed | `mcu_minimal/minimal.qml`, simplified gauge lineage |
| **reject** | Must fail with stable `DiagnosticCode` | `listmodel.qml`, `layouts/*.qml`, desktop `quick/` samples using unsupported APIs |
| **reference** | Human/visual baseline; not necessarily compilable by QVGL v1 | `studio_components/Gauge.qml`, `automotive/` cluster |

Our `turbo_gauge` is a **profile-reduced derivative** of the official Ultralite gauge pattern (dual arc → single `Arc` in IR), not a copy of `Gauge.qml` (gradients, `ArcItem`, timers).

---

## Repo layout

```text
examples/upstream/
  manifest.yaml          # canonical list: id, upstream path, tier, expect code
  README.md
tools/
  sync_upstream_examples.sh   # copy from local Qt install → examples/upstream/synced/
examples/upstream/synced/     # gitignored — local mirror for dev/CI with Qt installed
tests/fixtures/qml/reject/    # committed minimal rejects (no Qt install required)
```

**Do not commit** full Qt MCUs trees — license is often `LicenseRef-Qt-Commercial`. The manifest records **provenance**; CI/dev machines with Qt run `sync_upstream_examples.sh` before upstream pytest.

---

## Environment variables

| Variable | Default | Role |
|----------|---------|------|
| `QT_EXAMPLES` | `~/Qt/Examples/Qt-6.11.1` | Desktop Qt Quick examples root |
| `QTMCU` | `~/Qt/QtMCUs/2.12.1` | Qt for MCUs install root |

---

## Workflow

```bash
# 1. Sync upstream QML into gitignored mirror
./tools/sync_upstream_examples.sh

# 2. Check one file against profile
qvglc check examples/upstream/synced/mcu_minimal/minimal.qml
qvglc coverage examples/upstream/synced/mcu_listmodel/listmodel.qml   # expect reject

# 3. Run upstream tests (skip if sync dir missing)
pytest tests/python/test_upstream_examples.py
```

---

## Qt Creator alignment

1. Open Qt Creator → **Examples** → pick kit (e.g. Qt 6.11.1 or Qt for MCUs).
2. Note example name and path (e.g. `studio_components`, `minimal`).
3. Add or update entry in `examples/upstream/manifest.yaml` with that path relative to `QTMCU` or `QT_EXAMPLES`.
4. Set `tier` and expected `code` for reject entries.

This keeps QVGL’s end-to-end proof tied to the same files designers open in Creator.

---

## Upstream integration

| Step | Upstream role |
|------|----------------|
| Parser sema | `qvglc check` on every `tier: pass` synced example |
| IR golden | Start with `minimal.qml`; then turbo lineage vs hand golden |
| Render golden | After IR exists — PNG from LVGL vs Qt MCUs preview (manual/high-tol) |
| Reject proof | `tier: reject` + `test_upstream_examples.py` + `test_parser_reject.py` |
