from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "examples/conformance/manifest.yaml"
EMIT_MARKERS = ROOT / "examples/conformance/emit_markers.yaml"

KNOWN_TIERS = frozenset({"smoke", "pass", "partial", "reference", "reject"})


def load_manifest() -> list[dict]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data["cases"]


def load_emit_markers() -> dict[str, list[str]]:
    data = yaml.safe_load(EMIT_MARKERS.read_text(encoding="utf-8"))
    return {str(k): list(v) for k, v in data.items()}


def emit_tier_cases() -> list[dict]:
    return [c for c in load_manifest() if c["tier"] in ("smoke", "pass", "reference")]
