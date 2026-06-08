from __future__ import annotations

EMIT_KIND: dict[str, str] = {
    "Label": "Text",
}

LAYOUT_CONTAINERS = frozenset({"ColumnLayout", "RowLayout"})

LAYOUT_ATTACHED_PROPS = frozenset(
    {
        "fillWidth",
        "fillHeight",
        "preferredWidth",
        "preferredHeight",
        "minimumWidth",
        "minimumHeight",
        "alignment",
    }
)

PLOT_POINT_TYPE = "PlotPoint"

UNSUPPORTED_QML_TYPES = frozenset(
    {
        "Canvas",
        "Connections",
        "State",
        "PropertyChanges",
    }
)


def normalize_kind(type_name: str) -> str:
    return EMIT_KIND.get(type_name, type_name)
