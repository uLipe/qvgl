from __future__ import annotations

from qvglc.profile.load import Profile


def normalize_color(s: str) -> str:
    if not isinstance(s, str) or not s.startswith("#"):
        raise ValueError(f"invalid color: {s!r}")
    h = s[1:].lower()
    if len(h) == 6:
        return f"#ff{h}"
    if len(h) == 8:
        return f"#{h}"
    raise ValueError(f"invalid color: {s!r}")


def merge_theme_aliases(colors: dict[str, str], aliases: dict[str, str]) -> dict[str, str]:
    merged = dict(colors)
    for alias, target in aliases.items():
        if target not in merged:
            raise ValueError(f"theme alias {alias!r} points to unknown token {target!r}")
        merged[alias] = merged[target]
    return merged


def resolve_theme_member(profile: Profile, member: str) -> str:
    if member not in profile.theme_colors:
        raise KeyError(member)
    return normalize_color(profile.theme_colors[member])


def check_theme_member(
    namespace: str,
    member: str,
    profile: Profile,
    *,
    line: int = 0,
    column: int = 0,
) -> None:
    from qvglc.parser.errors import DiagnosticCode, QvglDiagnostic

    if member in profile.theme_colors:
        return
    raise QvglDiagnostic(
        DiagnosticCode.UNSUPPORTED_EXPR,
        f"unknown theme token {namespace}.{member} (not in profile theme.colors)",
        line,
        column,
    )
