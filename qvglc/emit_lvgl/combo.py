from __future__ import annotations

from qvglc.ir.model import Module, Node


def combo_model_items(node: Node) -> list[str]:
    model = node.properties.get("model")
    if not isinstance(model, list) or not model:
        return ["Item"]
    out: list[str] = []
    for item in model:
        if not isinstance(item, str):
            continue
        out.append(item)
    return out or ["Item"]


def combo_initial_index(node: Node, mod: Module) -> int:
    value = node.properties.get("currentIndex", 0)
    if isinstance(value, dict) and "binding" in value:
        sym = value["binding"].get("sym")
        if sym:
            for prop in mod.module_properties:
                if prop.name == sym and prop.default is not None:
                    return int(prop.default)
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def combo_options_c_literal(items: list[str]) -> str:
    escaped = [s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") for s in items]
    return "\\n".join(escaped)


def emit_combo_create(
    field: str,
    parent: str,
    geom: list[str],
    *,
    options: str,
    selected: int,
    handler_cbs: list[str],
) -> list[str]:
    lines = [
        f"    ui->{field} = lv_dropdown_create({parent});",
        *geom,
        f'    lv_dropdown_set_options(ui->{field}, "{options}");',
        f"    lv_dropdown_set_selected(ui->{field}, {selected});",
    ]
    for cb in handler_cbs:
        lines.append(
            f"    lv_obj_add_event_cb(ui->{field}, {cb}, LV_EVENT_VALUE_CHANGED, NULL);"
        )
    return lines
