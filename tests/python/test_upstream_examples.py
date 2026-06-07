from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from qvglc.coverage import coverage_report
from qvglc.parser import QvglDiagnostic, check_qml, default_profile_path, load_profile

ROOT = Path(__file__).resolve().parents[2]
SYNCED = ROOT / "examples/upstream/synced"
MANIFEST = ROOT / "examples/upstream/manifest.yaml"


def _manifest_entries():
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data["entries"]


def _qml_path(entry: dict) -> Path | None:
    fixture = entry.get("fixture")
    if fixture:
        p = ROOT / fixture
        if p.is_file():
            return p
    synced = SYNCED / entry["id"] / Path(entry["path"]).name
    if synced.is_file():
        return synced
    return None


@pytest.fixture(scope="module")
def profile():
    return load_profile(default_profile_path())


@pytest.mark.parametrize("entry", [e for e in _manifest_entries() if e["tier"] == "pass"])
def test_upstream_pass(entry, profile):
    path = _qml_path(entry)
    if path is None:
        pytest.skip(f"no QML for {entry['id']}")
    check_qml(path, profile)
    expected_sha = entry.get("fixture_sha256")
    if expected_sha and entry.get("fixture"):
        fixture = ROOT / entry["fixture"]
        if fixture.is_file():
            sha = hashlib.sha256(fixture.read_bytes()).hexdigest()
            assert sha == expected_sha


@pytest.mark.parametrize("entry", [e for e in _manifest_entries() if e["tier"] == "reject"])
def test_upstream_reject(entry, profile):
    path = _qml_path(entry)
    if path is None:
        pytest.skip(f"no synced reject for {entry['id']} (run sync_upstream_examples.sh)")
    expected = entry.get("expect_code")
    with pytest.raises(QvglDiagnostic) as exc:
        check_qml(path, profile)
    code = exc.value.code.value
    if expected:
        assert code in (expected, "parse_syntax"), f"got {code!r}: {exc.value}"


def test_mcu_minimal_coverage_cli():
    entry = next(e for e in _manifest_entries() if e["id"] == "mcu_minimal")
    path = _qml_path(entry)
    if path is None:
        pytest.skip("mcu_minimal fixture or sync missing")
    prof = load_profile(default_profile_path())
    ok, msg = coverage_report(path, prof)
    assert ok, msg
