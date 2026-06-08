from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from qvglc.parser import QvglDiagnostic, check_qml, load_profile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "examples/conformance/manifest.yaml"


def _load_cases() -> list[dict]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_conformance_tier(case: dict):
    qml = ROOT / case["qml"]
    profile = load_profile(ROOT / case["profile"])
    tier = case["tier"]

    assert qml.is_file(), f"missing {qml}"

    if tier == "reject":
        with pytest.raises(QvglDiagnostic) as exc:
            check_qml(qml, profile)
        expect = case.get("expect_code")
        if expect:
            assert exc.value.code.value == expect, exc.value
        return

    check_qml(qml, profile)

    if tier == "pass":
        return

    if tier == "partial":
        return

    if tier == "reference":
        return

    pytest.fail(f"unknown tier {tier!r}")
