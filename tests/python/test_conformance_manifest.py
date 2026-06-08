from __future__ import annotations

import pytest

from conformance_util import KNOWN_TIERS, load_manifest
from qvglc.conformance import validate_manifest
from qvglc.parser import QvglDiagnostic, check_qml, load_profile

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_schema_valid():
    errors = validate_manifest(load_manifest())
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("case", load_manifest(), ids=lambda c: c["id"])
def test_conformance_tier(case: dict):
    assert case["tier"] in KNOWN_TIERS
    qml = ROOT / case["qml"]
    profile = load_profile(ROOT / case["profile"])
    tier = case["tier"]

    if tier == "reject":
        with pytest.raises(QvglDiagnostic) as exc:
            check_qml(qml, profile)
        expect = case.get("expect_code")
        if expect:
            assert exc.value.code.value == expect, exc.value
        return

    check_qml(qml, profile)
