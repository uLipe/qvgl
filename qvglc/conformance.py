from __future__ import annotations

from pathlib import Path

import yaml

from qvglc.parser import QvglDiagnostic, check_qml, load_profile

KNOWN_TIERS = frozenset({"smoke", "pass", "partial", "reference", "reject"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(manifest: Path | None = None) -> list[dict]:
    path = manifest or (_repo_root() / "examples/conformance/manifest.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("manifest cases must be a list")
    return cases


def validate_manifest(cases: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        case_id = case.get("id")
        if not case_id:
            errors.append("case missing id")
            continue
        if case_id in seen:
            errors.append(f"duplicate case id {case_id!r}")
        seen.add(case_id)
        tier = case.get("tier")
        if tier not in KNOWN_TIERS:
            errors.append(f"{case_id}: unknown tier {tier!r}")
        qml = case.get("qml")
        if not qml:
            errors.append(f"{case_id}: missing qml path")
            continue
        if not (_repo_root() / qml).is_file():
            errors.append(f"{case_id}: missing file {qml}")
        profile = case.get("profile")
        if not profile:
            errors.append(f"{case_id}: missing profile")
        elif not (_repo_root() / profile).is_file():
            errors.append(f"{case_id}: missing profile file {profile}")
        if tier == "reject" and not case.get("expect_code"):
            errors.append(f"{case_id}: reject tier needs expect_code")
    return errors


def run_conformance_checks(
    manifest: Path | None = None,
    *,
    tier_filter: frozenset[str] | None = None,
) -> tuple[int, list[str]]:
    root = _repo_root()
    cases = load_manifest(manifest)
    errors = validate_manifest(cases)
    if errors:
        return 1, errors

    tiers = tier_filter or frozenset({"smoke", "pass", "partial", "reference", "reject"})
    for case in cases:
        tier = case["tier"]
        if tier not in tiers:
            continue
        qml = root / case["qml"]
        profile = load_profile(root / case["profile"])
        case_id = case["id"]
        try:
            if tier == "reject":
                check_qml(qml, profile)
                errors.append(f"{case_id}: expected reject but check passed")
            else:
                check_qml(qml, profile)
        except QvglDiagnostic as e:
            if tier == "reject":
                expect = case.get("expect_code")
                if expect and e.code.value != expect:
                    errors.append(f"{case_id}: expected {expect}, got {e.code.value}")
            else:
                errors.append(f"{case_id}: {e}")

    return (1 if errors else 0), errors
