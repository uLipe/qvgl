from __future__ import annotations

from pathlib import Path

import yaml

from qvglc.conformance import load_manifest, run_conformance_checks, validate_manifest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_qt_parity_manifest(path: Path | None = None) -> list[dict]:
    p = path or (_repo_root() / "examples/conformance/qt_parity.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("qt_parity cases must be a list")
    return cases


def load_emit_markers(path: Path | None = None) -> dict[str, list[str]]:
    p = path or (_repo_root() / "examples/conformance/emit_markers.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {str(k): list(v) for k, v in data.items()}


def load_reference_trim(path: Path | None = None) -> list[dict]:
    p = path or (_repo_root() / "examples/conformance/reference_trim.yaml")
    if not p.is_file():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    return cases if isinstance(cases, list) else []


def validate_qt_parity(root: Path | None = None) -> list[str]:
    root = root or _repo_root()
    errors: list[str] = []
    seen: set[str] = set()
    for case in load_qt_parity_manifest():
        case_id = case.get("id")
        if not case_id:
            errors.append("qt_parity: case missing id")
            continue
        if case_id in seen:
            errors.append(f"qt_parity: duplicate id {case_id!r}")
        seen.add(case_id)
        qml = case.get("qml")
        if not qml:
            errors.append(f"qt_parity:{case_id}: missing qml")
            continue
        if not (root / qml).is_file():
            errors.append(f"qt_parity:{case_id}: missing file {qml}")
        qt_qml = case.get("qt_qml", qml)
        if not (root / qt_qml).is_file():
            errors.append(f"qt_parity:{case_id}: missing qt file {qt_qml}")
        profile = case.get("profile")
        if not profile:
            errors.append(f"qt_parity:{case_id}: missing profile")
        elif not (root / profile).is_file():
            errors.append(f"qt_parity:{case_id}: missing profile file {profile}")
    return errors


def validate_emit_marker_coverage(root: Path | None = None) -> list[str]:
    root = root or _repo_root()
    markers = load_emit_markers()
    errors: list[str] = []
    for case in load_manifest():
        tier = case.get("tier")
        if tier not in ("smoke", "pass", "reference"):
            continue
        case_id = case["id"]
        if case_id not in markers:
            errors.append(f"{case_id}: missing emit_markers.yaml entry (tier {tier})")
        elif not markers[case_id]:
            errors.append(f"{case_id}: empty emit_markers list")
    return errors


def validate_reference_trim(root: Path | None = None) -> list[str]:
    root = root or _repo_root()
    errors: list[str] = []
    manifest_ids = {c["id"] for c in load_manifest() if c.get("tier") == "reference"}
    for entry in load_reference_trim():
        ref_id = entry.get("id")
        if not ref_id:
            errors.append("reference_trim: entry missing id")
            continue
        if ref_id not in manifest_ids:
            errors.append(f"reference_trim:{ref_id}: not a reference tier in manifest.yaml")
        derives = entry.get("derives_from")
        if derives and not (root / f"examples/{derives}/{derives}.qml").is_file():
            alt = next(
                (c["qml"] for c in load_manifest() if c["id"] == derives),
                None,
            )
            if not alt or not (root / alt).is_file():
                errors.append(f"reference_trim:{ref_id}: derives_from {derives!r} not found")
        qt_qml = entry.get("qt_qml")
        if qt_qml and not (root / qt_qml).is_file():
            errors.append(f"reference_trim:{ref_id}: missing qt_qml {qt_qml}")
    for ref_id in manifest_ids:
        if not any(e.get("id") == ref_id for e in load_reference_trim()):
            errors.append(f"reference_trim: missing entry for manifest reference {ref_id!r}")
    return errors


def run_proof_checks(
    *,
    manifest: Path | None = None,
    skip_reference_trim: bool = False,
) -> tuple[int, list[str]]:
    errors: list[str] = []
    errors.extend(validate_manifest(load_manifest(manifest)))

    code, conf_errors = run_conformance_checks(manifest)
    errors.extend(conf_errors)

    errors.extend(validate_emit_marker_coverage())
    errors.extend(validate_qt_parity())
    if not skip_reference_trim:
        errors.extend(validate_reference_trim())

    return (1 if errors else 0), errors
