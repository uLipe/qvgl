# Upstream Qt examples manifest

Lists **real** QML from the Qt SDK (same files Qt Creator shows under **Examples**).

See [docs/08-upstream-examples.md](../../docs/08-upstream-examples.md).

```bash
export QTMCU=~/Qt/QtMCUs/2.12.1
export QT_EXAMPLES=~/Qt/Examples/Qt-6.11.1
../../tools/sync_upstream_examples.sh
```

Synced files land in `synced/` (gitignored).
