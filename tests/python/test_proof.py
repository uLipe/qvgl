from __future__ import annotations

from pathlib import Path

from qvglc.proof import (
    load_reference_trim,
    run_proof_checks,
    validate_emit_marker_coverage,
    validate_qt_parity,
    validate_reference_trim,
)

ROOT = Path(__file__).resolve().parents[2]


def test_qt_parity_manifest_valid():
    assert not validate_qt_parity(ROOT)


def test_emit_markers_cover_manifest_tiers():
    assert not validate_emit_marker_coverage(ROOT)


def test_reference_trim_linked():
    entries = load_reference_trim()
    assert any(e["id"] == "channel_plot_trim" for e in entries)
    assert not validate_reference_trim(ROOT)


def test_proof_gate_passes():
    code, errors = run_proof_checks()
    assert code == 0, "\n".join(errors)
