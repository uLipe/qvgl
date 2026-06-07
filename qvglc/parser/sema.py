from __future__ import annotations

from typing import Any

from qvglc.profile.load import Profile

from .ast import Document, Object
from .errors import DiagnosticCode, QvglDiagnostic

_UNSUPPORTED_TYPES = frozenset(
    {
        "ListModel",
        "ListElement",
        "Component",
        "Timer",
        "Repeater",
    }
)

_ALLOWED_HANDLER_CALLS = frozenset({"app_on_gauge_clicked"})


def analyze(doc: Document, profile: Profile) -> None:
    if not doc.root:
        raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "missing root object")

    for imp in doc.imports:
        if imp.key not in profile.allowed_imports:
            raise QvglDiagnostic(
                DiagnosticCode.UNKNOWN_IMPORT,
                f"import {imp.key!r} not allowed by profile {profile.name!r}",
                imp.loc.line,
                imp.loc.column,
            )

    if not doc.imports:
        raise QvglDiagnostic(DiagnosticCode.UNKNOWN_IMPORT, "missing import QtQuick")

    _check_object(doc.root, profile, module_props={})


def _check_object(obj: Object, profile: Profile, module_props: dict[str, str]) -> None:
    if obj.type_name in ("State", "Connections", "PropertyChanges"):
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_FEATURE,
            f"feature {obj.type_name!r} is not supported",
            obj.loc.line,
            obj.loc.column,
        )

    if obj.type_name.endswith("Animation") and obj.type_name != "NumberAnimation":
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_TYPE,
            f"type {obj.type_name!r} is not supported",
            obj.loc.line,
            obj.loc.column,
        )

    if obj.type_name in _UNSUPPORTED_TYPES:
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_TYPE,
            f"type {obj.type_name!r} is not supported",
            obj.loc.line,
            obj.loc.column,
        )

    if profile.fail_on_unknown_type and obj.type_name not in profile.type_names():
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_TYPE,
            f"unknown type {obj.type_name!r}",
            obj.loc.line,
            obj.loc.column,
        )

    if obj.type_name == "ListView":
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_TYPE,
            "ListView is not supported",
            obj.loc.line,
            obj.loc.column,
        )

    props = module_props.copy()
    for name, val, loc in obj.properties:
        if name.startswith("property "):
            parts = name.split(" ")
            if len(parts) >= 3:
                props[parts[2]] = parts[1]
            continue
        if name.startswith("property"):
            continue
        if name.startswith("on") and name[2:3].isupper():
            _check_handler(val, loc)
            continue
        if name == "__on_property__":
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_FEATURE,
                "property animations are not supported",
                loc.line,
                loc.column,
            )
        if name.startswith("states") or name == "states":
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_FEATURE,
                "states are not supported",
                loc.line,
                loc.column,
            )
        if name.startswith("anchors."):
            anchor = name.split(".", 1)[1]
            if anchor not in profile.allowed_anchors and not anchor.endswith("Margin"):
                raise QvglDiagnostic(
                    DiagnosticCode.UNSUPPORTED_ANCHOR,
                    f"anchor {anchor!r} not in profile",
                    loc.line,
                    loc.column,
                )
            _check_expr(val, loc, props, profile)
            continue

        allowed = profile.properties_for(obj.type_name)
        if profile.fail_on_unknown_property and name not in allowed:
            raise QvglDiagnostic(
                DiagnosticCode.UNKNOWN_PROPERTY,
                f"property {name!r} not allowed on {obj.type_name!r}",
                loc.line,
                loc.column,
            )
        _check_expr(val, loc, props, profile)

    for child in obj.children:
        if child.type_name == "NumberAnimation":
            _check_number_animation(child, obj.type_name, profile)
            continue
        if child.type_name in _UNSUPPORTED_TYPES or child.type_name.endswith("Animation"):
            raise QvglDiagnostic(
                DiagnosticCode.UNKNOWN_TYPE,
                f"type {child.type_name!r} is not supported",
                child.loc.line,
                child.loc.column,
            )
        _check_object(child, profile, props)


def _animation_target(child: Object) -> str | None:
    for name, val, _ in child.properties:
        if name == "__on_property__":
            return str(val)
    return None


def _check_number_animation(child: Object, parent_type: str, profile: Profile) -> None:
    if "NumberAnimation" not in profile.allowed_animations:
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_FEATURE,
            "NumberAnimation is not allowed by profile",
            child.loc.line,
            child.loc.column,
        )
    if parent_type != "Arc":
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_FEATURE,
            "NumberAnimation is only supported on Arc",
            child.loc.line,
            child.loc.column,
        )
    target = _animation_target(child)
    if target != "value":
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_FEATURE,
            f"NumberAnimation on {target!r} is not supported (only Arc.value)",
            child.loc.line,
            child.loc.column,
        )
    duration = None
    for name, val, loc in child.properties:
        if name == "__on_property__":
            continue
        if name != "duration":
            raise QvglDiagnostic(
                DiagnosticCode.UNKNOWN_PROPERTY,
                f"NumberAnimation property {name!r} not supported",
                loc.line,
                loc.column,
            )
        if not isinstance(val, (int, float)) or val <= 0:
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                "NumberAnimation duration must be a positive number",
                loc.line,
                loc.column,
            )
        duration = int(val)
    if duration is None:
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_PROPERTY,
            "NumberAnimation requires duration",
            child.loc.line,
            child.loc.column,
        )


def _check_handler(val: Any, loc) -> None:
    if isinstance(val, dict) and val.get("op") == "call":
        callee = val.get("callee", "")
        if callee not in _ALLOWED_HANDLER_CALLS:
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                f"handler call {callee!r} not allowed",
                loc.line,
                loc.column,
            )
        return
    if isinstance(val, dict) and val.get("op") == "sym":
        if val.get("name") not in _ALLOWED_HANDLER_CALLS:
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                "handler must be a bare app callback call",
                loc.line,
                loc.column,
            )
        return
    raise QvglDiagnostic(
        DiagnosticCode.UNSUPPORTED_EXPR,
        "invalid signal handler",
        loc.line,
        loc.column,
    )


def _check_expr(val: Any, loc, props: dict[str, str], profile: Profile) -> None:
    if val is None or isinstance(val, (str, int, float, bool)):
        return
    if isinstance(val, Object):
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_FEATURE,
            "nested objects as property values require explicit support",
            loc.line,
            loc.column,
        )
    if not isinstance(val, dict):
        return

    op = val.get("op")
    if op == "sym":
        name = val.get("name", "")
        if name.startswith("Theme."):
            member = name.split(".", 1)[1]
            if member in profile.theme_colors:
                return
        if name.startswith("Image."):
            member = name.split(".", 1)[1]
            if member in ("Stretch", "PreserveAspectFit", "PreserveAspectCrop"):
                return
        if name not in props and name not in ("parent",):
            pass
        return
    if op == "const":
        return
    if op == "member":
        base = val.get("base", "")
        member = val.get("member", "")
        if base in ("Text", "Item") and member.startswith("Align"):
            return
        if base == "Theme" and member in profile.theme_colors:
            return
        if base == "Image" and member in ("Stretch", "PreserveAspectFit", "PreserveAspectCrop"):
            return
        if member in ("toFixed", "toPrecision"):
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                f"js-style call .{member}() is not allowed (use profile bindings)",
                loc.line,
                loc.column,
            )
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_EXPR,
            f"member access {base}.{member} not supported",
            loc.line,
            loc.column,
        )
    if op == "call":
        callee = val.get("callee", "")
        if callee.endswith(".toFixed") and len(val.get("args", [])) == 1:
            base = callee[: -len(".toFixed")]
            if base in props:
                return
        if callee.startswith("Math.") or "." in callee:
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                f"call {callee!r} not allowed",
                loc.line,
                loc.column,
            )
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_EXPR,
            f"call {callee!r} not allowed",
            loc.line,
            loc.column,
        )
    if op == "add":
        _check_expr(val.get("left"), loc, props, profile)
        _check_expr(val.get("right"), loc, props, profile)
        return
    raise QvglDiagnostic(
        DiagnosticCode.UNSUPPORTED_EXPR,
        f"expression op {op!r} not allowed",
        loc.line,
        loc.column,
    )
