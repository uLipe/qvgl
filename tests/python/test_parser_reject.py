from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from qvglc.parser import QvglDiagnostic, check_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
REJECT_DIR = ROOT / "tests/fixtures/qml/reject"
MANIFEST = REJECT_DIR / "manifest.yaml"


def _reject_cases():
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    for case in data["cases"]:
        yield pytest.param(
            REJECT_DIR / case["file"],
            case["code"],
            id=case["file"],
        )


@pytest.fixture(scope="module")
def profile():
    return load_profile(default_profile_path())


@pytest.mark.parametrize("qml_path,expected_code", list(_reject_cases()))
def test_reject_unsupported_qml(qml_path: Path, expected_code: str, profile):
    with pytest.raises(QvglDiagnostic) as exc:
        check_qml(qml_path, profile)
    assert exc.value.code.value == expected_code, str(exc.value)


def test_turbo_gauge_parses_and_sema_ok(profile):
    qml = ROOT / "examples/turbo_gauge/turbo_gauge.qml"
    check_qml(qml, profile)


def test_static_card_parses(profile):
    check_qml(ROOT / "examples/static_card/static_card.qml", profile)


def test_bound_label_parses(profile):
    check_qml(ROOT / "examples/bound_label/bound_label.qml", profile)
