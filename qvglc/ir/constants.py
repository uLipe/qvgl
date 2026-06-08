QVGLIR_MAGIC = 0x31564751
QVGLIR_VERSION = 1
QVGL_NODE_NO_PARENT = 0xFFFFFFFF
QVGL_STR_NONE = 0

NODE_KIND = {
    "Item": 0,
    "Rectangle": 1,
    "Text": 2,
    "Image": 3,
    "Arc": 4,
    "Meter": 5,
    "MouseArea": 6,
    "Label": 7,
    "ToolButton": 8,
    "ColumnLayout": 9,
    "RowLayout": 10,
    "LinePlot": 11,
    "Slider": 12,
    "Switch": 13,
    "CheckBox": 14,
    "Button": 15,
    "ComboBox": 16,
}

NODE_KIND_NAME = {v: k for k, v in NODE_KIND.items()}

VAL_KIND = {
    "bool": 0,
    "i32": 1,
    "f32": 2,
    "color": 3,
    "string": 4,
    "enum": 5,
    "binding": 6,
    "anchors": 7,
}

EXPR_KIND = {
    "sym": 0,
    "const_i32": 1,
    "const_f32": 2,
    "const_str": 3,
    "add": 4,
    "sub": 5,
    "mul": 6,
    "ternary": 7,
    "map_linear": 8,
    "format": 9,
}

EXPR_OP = {
    "add": 4,
    "sub": 5,
    "mul": 6,
    "ternary": 7,
    "map_linear": 8,
    "format": 9,
}

NODE_F_STATIC_LAYOUT = 1 << 0
NODE_F_NEEDS_OBSERVER = 1 << 1

MODULE_TYPE = {
    "bool": 0,
    "i32": 1,
    "f32": 2,
    "string": 4,
    "color": 3,
}
