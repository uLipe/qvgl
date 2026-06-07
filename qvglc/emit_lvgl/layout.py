from __future__ import annotations

from qvglc.ir.model import Module
from qvglc.layout import NodeLayout, Rect, resolve_layout


def layout_module(mod: Module) -> dict[int, NodeLayout]:
    return resolve_layout(mod)


def layout_turbo_gauge(mod: Module) -> dict[int, NodeLayout]:
    return resolve_layout(mod)


def layout_minimal(mod: Module) -> dict[int, NodeLayout]:
    return resolve_layout(mod)
