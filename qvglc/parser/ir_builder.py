from __future__ import annotations

from typing import Any

from qvglc.ir.model import Binding, Handler, Module, ModuleProperty, Node
from qvglc.profile.load import Profile

from .ast import Document, Object
from .errors import DiagnosticCode, QvglDiagnostic

_PROP_TYPE_MAP = {
    "real": "f32",
    "int": "i32",
    "bool": "bool",
    "string": "str",
    "var": "f32",
}

_LAYOUT_ONLY_PROPS = frozenset({"horizontalAlignment", "verticalAlignment"})


def build_ir(doc: Document, profile: Profile, module_name: str) -> Module:
    if not doc.root:
        raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "missing root object")
    builder = _Builder(profile, module_name)
    root_idx = builder.build_object(doc.root, is_root=True)
    return Module(
        version=profile.version,
        profile=profile.name,
        module=module_name,
        root=root_idx,
        nodes=builder.nodes,
        module_properties=builder.module_properties,
        bindings=builder.bindings,
        handlers=builder.handlers,
    )


class _Builder:
    def __init__(self, profile: Profile, module_name: str) -> None:
        self.profile = profile
        self.module_name = module_name
        self.nodes: list[Node] = []
        self.module_properties: list[ModuleProperty] = []
        self.bindings: list[Binding] = []
        self.handlers: list[Handler] = []

    def _apply_arc_value_animation(self, arc_node: Node, anim: Object) -> None:
        for name, val, loc in anim.properties:
            if name == "__on_property__":
                continue
            if name == "duration":
                arc_node.properties["valueAnimationDuration"] = int(val)
                return
            raise QvglDiagnostic(
                DiagnosticCode.UNKNOWN_PROPERTY,
                f"NumberAnimation property {name!r} not supported",
                loc.line,
                loc.column,
            )
        raise QvglDiagnostic(
            DiagnosticCode.UNKNOWN_PROPERTY,
            "NumberAnimation requires duration",
            anim.loc.line,
            anim.loc.column,
        )

    def build_object(self, obj: Object, *, is_root: bool) -> int:
        idx = len(self.nodes)
        node = Node(kind=obj.type_name, id=obj.object_id)
        self.nodes.append(node)

        if is_root:
            self._collect_module_properties(obj)

        for child in obj.children:
            if child.type_name == "NumberAnimation":
                self._apply_arc_value_animation(node, child)
                continue
            child_idx = self.build_object(child, is_root=False)
            node.children.append(child_idx)
            self.nodes[child_idx].parent = idx

        anchors: dict[str, Any] = {}

        for name, val, loc in obj.properties:
            if name.startswith("property "):
                continue
            if name.startswith("anchors."):
                anchors[name.split(".", 1)[1]] = _lower_anchor(val)
                continue
            if name == "id":
                continue
            if name in _LAYOUT_ONLY_PROPS:
                continue
            if name.startswith("on") and len(name) > 2 and name[2].isupper():
                self._add_handler(node, name, val, loc)
                continue
            lowered = _lower_property_value(val, self.profile, loc)
            if isinstance(lowered, dict) and "binding" in lowered:
                node.properties[name] = lowered
                if node.id:
                    self.bindings.append(
                        Binding(target=node.id, key=name, expr=lowered["binding"])
                    )
                continue
            node.properties[name] = lowered

        if anchors:
            node.properties["anchors"] = anchors

        if is_root:
            self._apply_root_display_defaults(node)
        else:
            has_binding = any("binding" in v for v in node.properties.values() if isinstance(v, dict))
            node.flags.append("needs_observer" if has_binding else "static_layout")

        return idx

    def _apply_root_display_defaults(self, node: Node) -> None:
        if "width" not in node.properties:
            node.properties["width"] = self.profile.display_width
        if "height" not in node.properties:
            node.properties["height"] = self.profile.display_height

    def _collect_module_properties(self, obj: Object) -> None:
        for name, val, _loc in obj.properties:
            if not name.startswith("property "):
                continue
            parts = name.split()
            if len(parts) < 3:
                continue
            qml_type = parts[1]
            prop_name = parts[2]
            ir_type = _PROP_TYPE_MAP.get(qml_type)
            if ir_type is None:
                raise QvglDiagnostic(
                    DiagnosticCode.UNSUPPORTED_EXPR,
                    f"unsupported property type {qml_type!r}",
                )
            default = _lower_literal(val) if not isinstance(val, dict) else val.get("value")
            self.module_properties.append(
                ModuleProperty(name=prop_name, type=ir_type, default=default)
            )

    def _add_handler(self, node: Node, prop: str, val: Any, loc) -> None:
        if not node.id:
            raise QvglDiagnostic(
                DiagnosticCode.UNSUPPORTED_EXPR,
                "signal handler requires object id",
                loc.line,
                loc.column,
            )
        handler_name = _handler_callee(val)
        signal = prop[2:]
        signal = signal[0].lower() + signal[1:] if signal else signal
        self.handlers.append(Handler(node=node.id, signal=signal, handler=handler_name))


def _handler_callee(val: Any) -> str:
    if isinstance(val, dict) and val.get("op") == "call":
        return str(val.get("callee", ""))
    if isinstance(val, dict) and val.get("op") == "sym":
        return str(val.get("name", ""))
    raise QvglDiagnostic(DiagnosticCode.UNSUPPORTED_EXPR, "invalid signal handler")


def _lower_anchor(val: Any) -> Any:
    if isinstance(val, dict) and val.get("op") == "sym":
        return val["name"]
    if isinstance(val, dict) and val.get("op") == "member":
        return f"{val['base']}.{val['member']}"
    if isinstance(val, (int, float)):
        return int(val) if isinstance(val, int) or val == int(val) else val
    if isinstance(val, str):
        return val
    raise QvglDiagnostic(DiagnosticCode.UNSUPPORTED_EXPR, f"unsupported anchor value {val!r}")


def _lower_literal(val: Any) -> Any:
    if isinstance(val, str) and val.startswith("#"):
        return _normalize_color(val)
    return val


def _resolve_theme_member(profile: Profile, member: str, loc) -> str:
    if member not in profile.theme_colors:
        raise QvglDiagnostic(
            DiagnosticCode.UNSUPPORTED_EXPR,
            f"unknown theme token Theme.{member}",
            loc.line,
            loc.column,
        )
    return _normalize_color(profile.theme_colors[member])


def _lower_property_value(val: Any, profile: Profile, loc) -> Any:
    if isinstance(val, dict) and val.get("op") == "member":
        base = val.get("base", "")
        member = val.get("member", "")
        if base == "Theme":
            return _resolve_theme_member(profile, member, loc)
        if base == "Image" and member in ("Stretch", "PreserveAspectFit", "PreserveAspectCrop"):
            return member
    if isinstance(val, dict) and val.get("op") == "sym":
        name = val.get("name", "")
        if name.startswith("Theme."):
            return _resolve_theme_member(profile, name.split(".", 1)[1], loc)
        if name.startswith("Image."):
            member = name.split(".", 1)[1]
            if member in ("Stretch", "PreserveAspectFit", "PreserveAspectCrop"):
                return member
    if isinstance(val, dict) and "op" in val:
        expr = _lower_expr(val, loc)
        return {"binding": expr}
    return _lower_literal(val)


def _normalize_color(s: str) -> str:
    h = s[1:].lower()
    if len(h) == 6:
        return f"#ff{h}"
    if len(h) == 8:
        return f"#{h}"
    return s


def _lower_expr(expr: dict[str, Any], loc) -> dict[str, Any]:
    op = expr.get("op")
    if op == "sym":
        return {"sym": expr["name"]}
    if op == "const":
        return {"const": expr["value"]}
    if op == "add":
        fmt = _try_format_from_add(expr)
        if fmt:
            return fmt
    raise QvglDiagnostic(
        DiagnosticCode.UNSUPPORTED_EXPR,
        f"cannot lower expression op {op!r}",
        loc.line,
        loc.column,
    )


def _try_format_from_add(expr: dict[str, Any]) -> dict[str, Any] | None:
    left = expr.get("left")
    right = expr.get("right")
    if not isinstance(left, dict) or not isinstance(right, dict):
        return None
    if right.get("op") != "const" or not isinstance(right.get("value"), str):
        return None
    if left.get("op") != "call":
        return None
    callee = left.get("callee", "")
    if not callee.endswith(".toFixed"):
        return None
    base = callee[: -len(".toFixed")]
    args = left.get("args", [])
    if len(args) != 1 or args[0].get("op") != "const":
        return None
    prec = args[0]["value"]
    suffix = right["value"]
    return {
        "op": "format",
        "args": [{"const": f"%.{prec}f{suffix}"}, {"sym": base}],
    }
