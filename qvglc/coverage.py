from __future__ import annotations

from pathlib import Path

from qvglc.parser import QvglDiagnostic, check_qml, default_profile_path, load_profile
from qvglc.profile import Profile


def coverage_report(path: Path, profile: Profile | None = None) -> tuple[bool, str]:
    if profile is None:
        profile = load_profile(default_profile_path())
    try:
        check_qml(path, profile)
        return True, f"ok: {path} (profile {profile.name})"
    except QvglDiagnostic as e:
        return False, str(e)
