from __future__ import annotations

from pathlib import Path

from qvglc.profile import Profile, default_profile_path, load_profile

from .errors import DiagnosticCode, QvglDiagnostic
from .ir_builder import build_ir
from .parser import parse_qml
from .sema import analyze

__all__ = [
    "DiagnosticCode",
    "QvglDiagnostic",
    "Profile",
    "analyze",
    "build_ir",
    "check_qml",
    "compile_qml",
    "default_profile_path",
    "load_profile",
    "parse_qml",
]


def check_qml(source: str | Path, profile: Profile | None = None) -> None:
    if profile is None:
        profile = load_profile(default_profile_path())
    if isinstance(source, Path):
        source = source.read_text(encoding="utf-8")
    doc = parse_qml(source)
    analyze(doc, profile)


def compile_qml(
    source: str | Path,
    profile: Profile | None = None,
    module_name: str | None = None,
):
    if profile is None:
        profile = load_profile(default_profile_path())
    path = source if isinstance(source, Path) else None
    if isinstance(source, Path):
        source = source.read_text(encoding="utf-8")
    doc = parse_qml(source)
    analyze(doc, profile)
    name = module_name or (path.stem if path else "module")
    return build_ir(doc, profile, name)
