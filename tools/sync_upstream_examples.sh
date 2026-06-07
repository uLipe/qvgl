#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/examples/upstream/manifest.yaml"
OUT="$ROOT/examples/upstream/synced"

QT_EXAMPLES="${QT_EXAMPLES:-$HOME/Qt/Examples/Qt-6.11.1}"
QTMCU="${QTMCU:-$HOME/Qt/QtMCUs/2.12.1}"

if ! command -v python3 >/dev/null; then
    echo "python3 required" >&2
    exit 1
fi

python3 - "$MANIFEST" "$OUT" "$QT_EXAMPLES" "$QTMCU" <<'PY'
import hashlib
import shutil
import sys
from pathlib import Path

import yaml

manifest_path, out_root, qt_examples, qtmcu = sys.argv[1:5]
out_root = Path(out_root)
roots = {
    "qt_examples": Path(qt_examples).expanduser(),
    "qtmcu": Path(qtmcu).expanduser(),
}

data = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8"))
out_root.mkdir(parents=True, exist_ok=True)
index = []

for entry in data["entries"]:
    eid = entry["id"]
    base = roots[entry["root"]]
    src = base / entry["path"]
    dst_dir = out_root / eid
    dst = dst_dir / Path(entry["path"]).name
    if not src.is_file():
        print(f"skip missing: {src}", file=sys.stderr)
        continue
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    index.append({
        "id": eid,
        "tier": entry["tier"],
        "upstream": str(src),
        "synced": str(dst.relative_to(out_root.parent.parent.parent)),
        "sha256_16": digest,
        "expect_code": entry.get("expect_code"),
    })
    print(f"synced {eid} <- {src}")

(out_root / "index.yaml").write_text(
    yaml.dump({"entries": index}, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

echo "done -> $OUT"
