from __future__ import annotations

import struct
from typing import Any

from .constants import (
    MODULE_TYPE,
    NODE_F_NEEDS_OBSERVER,
    NODE_F_STATIC_LAYOUT,
    NODE_KIND,
    NODE_KIND_NAME,
    QVGLIR_MAGIC,
    QVGLIR_VERSION,
    QVGL_NODE_NO_PARENT,
    QVGL_STR_NONE,
    VAL_KIND,
)
from .expr import EncodedExpr, ExprTable
from .json_load import load_json_data
from .model import Binding, Handler, Module, ModuleProperty, Node
from .string_pool import StringPool
from .util import bits_f32, fnv1a32, f32_bits, parse_color
from .validate import validate

_HEADER_FMT = "<IHH" + "I" * 18
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
_NODE_FMT = "<HHIIIIHH IHH"
_PROP_FMT = "<I HHI"
_MOD_PROP_FMT = "<I HHI"
_BINDING_FMT = "<IIIHH"
_EXPR_FMT = "<HH" + "I" * 8
_HANDLER_FMT = "<IIIHH"


def encode_module(module: Module) -> bytes:
    validate(module)

    pool = StringPool()
    pool.add(module.profile)
    pool.add(module.module)
    expr_tab = ExprTable(pool)

    id_to_index = {n.id: i for i, n in enumerate(module.nodes) if n.id}

    flat_bindings: list[tuple[int, str, int]] = []
    for b in module.bindings:
        flat_bindings.append((id_to_index[b.target], b.key, expr_tab.add_json(b.expr)))

    node_props: list[list[tuple[int, int, int]]] = [[] for _ in module.nodes]
    for i, node in enumerate(module.nodes):
        for key, val in node.properties.items():
            vk, vv = _encode_property_value(val, pool, expr_tab)
            node_props[i].append((pool.add(key), vk, 0, vv))

    props_flat: list[tuple[int, int, int, int]] = []
    prop_off: list[int] = []
    prop_count: list[int] = []
    for plist in node_props:
        prop_off.append(len(props_flat))
        prop_count.append(len(plist))
        props_flat.extend(plist)

    mod_props_enc: list[tuple[int, int, int, int]] = []
    for mp in module.module_properties:
        t = MODULE_TYPE[mp.type]
        default = 0
        if mp.default is not None:
            if mp.type == "f32":
                default = f32_bits(float(mp.default))
            elif mp.type == "i32":
                default = int(mp.default) & 0xFFFFFFFF
            elif mp.type == "bool":
                default = 1 if mp.default else 0
            elif mp.type == "string":
                default = pool.add(str(mp.default))
            elif mp.type == "color":
                default = parse_color(str(mp.default))
        mod_props_enc.append((pool.add(mp.name), t, 0, default))

    bindings_enc: list[tuple[int, int, int, int, int]] = []
    for node_i, key, expr_i in flat_bindings:
        bindings_enc.append((node_i, pool.add(key), expr_i, 0, 0))

    handlers_enc: list[tuple[int, int, int, int, int]] = []
    for h in module.handlers:
        handlers_enc.append(
            (id_to_index[h.node], pool.add(h.signal), pool.add(h.handler), 0, 0)
        )

    nodes_enc: list[tuple] = []
    for i, node in enumerate(module.nodes):
        flags = 0
        if "static_layout" in node.flags:
            flags |= NODE_F_STATIC_LAYOUT
        if "needs_observer" in node.flags:
            flags |= NODE_F_NEEDS_OBSERVER
        children = node.children
        child_first = children[0] if children else 0
        parent = node.parent if node.parent >= 0 else QVGL_NODE_NO_PARENT
        nodes_enc.append(
            (
                NODE_KIND[node.kind],
                flags,
                pool.add(node.name) if node.name else QVGL_STR_NONE,
                pool.add(node.id) if node.id else QVGL_STR_NONE,
                parent,
                child_first,
                len(children),
                0,
                prop_off[i],
                prop_count[i],
                0,
            )
        )

    str_blob = pool.encode()
    str_off = _HEADER_SIZE

    sections = [
        str_blob,
        _pack_many(_NODE_FMT, nodes_enc),
        _pack_many(_PROP_FMT, props_flat),
        _pack_many(_MOD_PROP_FMT, mod_props_enc),
        _pack_many(_BINDING_FMT, bindings_enc),
        _pack_exprs(expr_tab.exprs),
        _pack_many(_HANDLER_FMT, handlers_enc),
    ]

    offsets = []
    pos = str_off
    for blob in sections:
        offsets.append(pos)
        pos += len(blob)

    (
        _,
        node_off,
        prop_off_b,
        mod_prop_off,
        binding_off,
        expr_off,
        handler_off,
    ) = offsets

    header = struct.pack(
        _HEADER_FMT,
        QVGLIR_MAGIC,
        QVGLIR_VERSION,
        0,
        fnv1a32(module.profile),
        pool.add(module.module),
        module.root,
        pool.count,
        str_off,
        len(nodes_enc),
        node_off,
        len(props_flat),
        prop_off_b,
        len(mod_props_enc),
        mod_prop_off,
        len(bindings_enc),
        binding_off,
        len(expr_tab.exprs),
        expr_off,
        len(handlers_enc),
        handler_off,
        pos,
    )

    return header + b"".join(sections)


def decode_binary(data: bytes) -> Module:
    if len(data) < _HEADER_SIZE:
        raise ValueError("truncated header")

    fields = struct.unpack(_HEADER_FMT, data[:_HEADER_SIZE])
    magic, version = fields[0], fields[1]
    if magic != QVGLIR_MAGIC:
        raise ValueError(f"bad magic 0x{magic:08x}")
    if version != QVGLIR_VERSION:
        raise ValueError(f"unsupported version {version}")

    profile_hash = fields[3]
    module_name_i = fields[4]
    root_node = fields[5]
    str_count = fields[6]
    str_off = fields[7]
    node_count = fields[8]
    node_off = fields[9]
    prop_count = fields[10]
    prop_off = fields[11]
    mod_prop_count = fields[12]
    mod_prop_off = fields[13]
    binding_count = fields[14]
    binding_off = fields[15]
    expr_count = fields[16]
    expr_off = fields[17]
    handler_count = fields[18]
    handler_off = fields[19]
    file_size = fields[20]

    if file_size != len(data):
        raise ValueError(f"file_size {file_size} != len {len(data)}")

    pool = StringPool.decode(data[str_off:node_off], str_count)

    nodes_raw = _unpack_many(_NODE_FMT, data[node_off:prop_off], node_count)
    props_raw = _unpack_many(_PROP_FMT, data[prop_off:mod_prop_off], prop_count)
    mod_props_raw = _unpack_many(_MOD_PROP_FMT, data[mod_prop_off:binding_off], mod_prop_count)
    bindings_raw = _unpack_many(_BINDING_FMT, data[binding_off:expr_off], binding_count)
    exprs_raw = _unpack_exprs(data[expr_off:handler_off], expr_count)
    handlers_raw = _unpack_many(_HANDLER_FMT, data[handler_off:file_size], handler_count)

    nodes: list[Node] = []
    for kind, flags, name, nid, parent, child_first, child_count, _, poff, pcount, _ in nodes_raw:
        children = list(range(child_first, child_first + child_count))
        node_flags = []
        if flags & NODE_F_STATIC_LAYOUT:
            node_flags.append("static_layout")
        if flags & NODE_F_NEEDS_OBSERVER:
            node_flags.append("needs_observer")
        props = {}
        for i in range(poff, poff + pcount):
            key_i, vk, _, vv = props_raw[i]
            props[pool.get(key_i)] = _decode_property_value(vk, vv, pool, exprs_raw)
        nodes.append(
            Node(
                kind=NODE_KIND_NAME[kind],
                children=children,
                id=pool.get(nid) if nid != QVGL_STR_NONE else None,
                name=pool.get(name) if name != QVGL_STR_NONE else None,
                properties=props,
                flags=node_flags,
                parent=parent if parent != QVGL_NODE_NO_PARENT else -1,
            )
        )

    module_properties: list[ModuleProperty] = []
    for name_i, typ, _, default in mod_props_raw:
        tname = {v: k for k, v in MODULE_TYPE.items()}[typ]
        default_val: Any = default
        if tname == "f32":
            default_val = bits_f32(default)
        elif tname == "bool":
            default_val = bool(default)
        elif tname == "string":
            default_val = pool.get(default)
        module_properties.append(ModuleProperty(name=pool.get(name_i), type=tname, default=default_val))

    id_by_index = {n.id: i for i, n in enumerate(nodes) if n.id}
    bindings: list[Binding] = []
    for target_node, key_i, expr_i, _, _ in bindings_raw:
        target_id = nodes[target_node].id
        if not target_id:
            raise ValueError("binding on node without id")
        bindings.append(
            Binding(
                target=target_id,
                key=pool.get(key_i),
                expr=_expr_to_json(exprs_raw[expr_i], pool, exprs_raw),
            )
        )

    handlers: list[Handler] = []
    for node_i, sig_i, handler_i, _, _ in handlers_raw:
        node_id = nodes[node_i].id
        if not node_id:
            raise ValueError("handler on node without id")
        handlers.append(
            Handler(
                node=node_id,
                signal=pool.get(sig_i),
                handler=pool.get(handler_i),
            )
        )

    profile = _profile_from_hash(profile_hash, pool)

    return Module(
        version=version,
        profile=profile,
        module=pool.get(module_name_i),
        root=root_node,
        nodes=nodes,
        module_properties=module_properties,
        bindings=bindings,
        handlers=handlers,
    )


def _profile_from_hash(profile_hash: int, pool: StringPool) -> str:
    for i in range(pool.count):
        s = pool.get(i)
        if fnv1a32(s) == profile_hash:
            return s
    return f"hash_{profile_hash:08x}"


def _encode_property_value(val: Any, pool: StringPool, expr_tab: ExprTable) -> tuple[int, int]:
    if isinstance(val, dict) and "binding" in val:
        return VAL_KIND["binding"], expr_tab.add_json(val["binding"])
    if isinstance(val, bool):
        return VAL_KIND["bool"], 1 if val else 0
    if isinstance(val, int):
        return VAL_KIND["i32"], val & 0xFFFFFFFF
    if isinstance(val, float):
        return VAL_KIND["f32"], f32_bits(val)
    if isinstance(val, str):
        if val.startswith("#"):
            return VAL_KIND["color"], parse_color(val)
        return VAL_KIND["string"], pool.add(val)
    if isinstance(val, dict) and "binding" not in val:
        import json

        if all(isinstance(v, (str, int, float, bool)) for v in val.values()):
            return VAL_KIND["anchors"], pool.add(
                json.dumps(val, sort_keys=True, separators=(",", ":"))
            )
    raise ValueError(f"unsupported property value: {val!r}")


def _decode_property_value(vk: int, vv: int, pool: StringPool, exprs: list[EncodedExpr]) -> Any:
    if vk == VAL_KIND["bool"]:
        return bool(vv)
    if vk == VAL_KIND["i32"]:
        return vv if vv < 0x80000000 else vv - 0x100000000
    if vk == VAL_KIND["f32"]:
        return bits_f32(vv)
    if vk == VAL_KIND["color"]:
        return f"#{vv:08x}"
    if vk == VAL_KIND["string"]:
        return pool.get(vv)
    if vk == VAL_KIND["binding"]:
        return {"binding": _expr_to_json(exprs[vv], pool, exprs)}
    if vk == VAL_KIND["anchors"]:
        import json

        return json.loads(pool.get(vv))
    raise ValueError(f"unsupported value kind {vk}")


def _expr_to_json(enc: EncodedExpr, pool: StringPool, exprs: list[EncodedExpr]) -> dict[str, Any]:
    from .constants import EXPR_KIND

    inv = {v: k for k, v in EXPR_KIND.items()}
    kind_name = inv[enc.kind]
    if kind_name == "sym":
        return {"sym": pool.get(enc.args[0])}
    if kind_name == "const_i32":
        v = enc.args[0]
        return {"const": v if v < 0x80000000 else v - 0x100000000}
    if kind_name == "const_f32":
        return {"const": bits_f32(enc.args[0])}
    if kind_name == "const_str":
        return {"const": pool.get(enc.args[0])}
    op = kind_name
    return {"op": op, "args": [_expr_to_json(exprs[a], pool, exprs) for a in enc.args[: enc.arity]]}


def _pack_many(fmt: str, rows: list[tuple]) -> bytes:
    return b"".join(struct.pack(fmt, *row) for row in rows)


def _unpack_many(fmt: str, blob: bytes, count: int) -> list[tuple]:
    size = struct.calcsize(fmt)
    if len(blob) != count * size:
        raise ValueError(f"section size mismatch: {len(blob)} != {count}*{size}")
    return [struct.unpack(fmt, blob[i * size : (i + 1) * size]) for i in range(count)]


def _pack_exprs(exprs: list[EncodedExpr]) -> bytes:
    out = bytearray()
    for e in exprs:
        args = list(e.args[:8]) + [0] * (8 - min(len(e.args), 8))
        out.extend(struct.pack(_EXPR_FMT, e.kind, e.arity, *args[:8]))
    return bytes(out)


def _unpack_exprs(blob: bytes, count: int) -> list[EncodedExpr]:
    size = struct.calcsize(_EXPR_FMT)
    exprs = []
    for i in range(count):
        kind, arity, *args = struct.unpack(_EXPR_FMT, blob[i * size : (i + 1) * size])
        exprs.append(EncodedExpr(kind, arity, list(args[:arity])))
    return exprs


def load_binary_path(path: str) -> Module:
    with open(path, "rb") as f:
        return decode_binary(f.read())


def write_binary_path(module: Module, path: str) -> None:
    data = encode_module(module)
    with open(path, "wb") as f:
        f.write(data)
