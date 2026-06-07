from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .constants import EXPR_KIND, EXPR_OP
from .string_pool import StringPool
from .util import f32_bits


@dataclass
class EncodedExpr:
    kind: int
    arity: int
    args: list[int]


class ExprTable:
    def __init__(self, pool: StringPool) -> None:
        self.pool = pool
        self.exprs: list[EncodedExpr] = []
        self._cache: dict[str, int] = {}

    def add_json(self, expr: dict[str, Any]) -> int:
        key = json.dumps(expr, sort_keys=True, separators=(",", ":"))
        if key in self._cache:
            return self._cache[key]

        if "sym" in expr:
            enc = EncodedExpr(EXPR_KIND["sym"], 1, [self.pool.add(expr["sym"])])
        elif "const" in expr:
            c = expr["const"]
            if isinstance(c, bool):
                enc = EncodedExpr(EXPR_KIND["const_i32"], 1, [1 if c else 0])
            elif isinstance(c, int):
                enc = EncodedExpr(EXPR_KIND["const_i32"], 1, [c & 0xFFFFFFFF])
            elif isinstance(c, float):
                enc = EncodedExpr(EXPR_KIND["const_f32"], 1, [f32_bits(c)])
            elif isinstance(c, str):
                enc = EncodedExpr(EXPR_KIND["const_str"], 1, [self.pool.add(c)])
            else:
                raise ValueError(f"unsupported const type: {type(c)}")
        elif "op" in expr:
            op = expr["op"]
            if op not in EXPR_OP:
                raise ValueError(f"unknown expr op {op!r}")
            args = [self.add_json(a) for a in expr["args"]]
            enc = EncodedExpr(EXPR_OP[op], len(args), args)
        else:
            raise ValueError(f"invalid expr: {expr!r}")

        idx = len(self.exprs)
        self.exprs.append(enc)
        self._cache[key] = idx
        return idx
