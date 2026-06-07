from __future__ import annotations

import json
from pathlib import Path

import pytest

from qvglc.ir import decode_binary, encode_module, load_json_path, module_to_dict, validate
from qvglc.ir.constants import QVGLIR_MAGIC, QVGLIR_VERSION

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_JSON = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir.json"
GOLDEN_BIN = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir"


def _norm_float(x: float) -> float:
    return float(f"{x:.6g}")


def _normalize_obj(obj):
    if isinstance(obj, float):
        return _norm_float(obj)
    if isinstance(obj, dict):
        return {k: _normalize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_obj(v) for v in obj]
    return obj


def _normalize(d: dict) -> dict:
    return json.loads(json.dumps(_normalize_obj(d), sort_keys=True))


def test_constants():
    assert QVGLIR_MAGIC == 0x31564751
    assert QVGLIR_VERSION == 1


def test_validate_golden():
    mod = load_json_path(GOLDEN_JSON)
    validate(mod)


def test_json_binary_roundtrip():
    mod = load_json_path(GOLDEN_JSON)
    blob = encode_module(mod)
    back = decode_binary(blob)
    validate(back)
    assert _normalize(module_to_dict(mod)) == _normalize(module_to_dict(back))


def test_binary_roundtrip_twice():
    mod = load_json_path(GOLDEN_JSON)
    b1 = encode_module(mod)
    m1 = decode_binary(b1)
    b2 = encode_module(m1)
    m2 = decode_binary(b2)
    assert b1 == b2
    assert _normalize(module_to_dict(m1)) == _normalize(module_to_dict(m2))


def test_committed_golden_binary():
    if not GOLDEN_BIN.is_file():
        pytest.skip("golden binary not committed")
    mod = load_json_path(GOLDEN_JSON)
    back = decode_binary(GOLDEN_BIN.read_bytes())
    assert _normalize(module_to_dict(back)) == _normalize(module_to_dict(mod))


def test_golden_binary_matches_json(tmp_path: Path):
    mod = load_json_path(GOLDEN_JSON)
    out = tmp_path / "turbo_gauge.qvglir"
    out.write_bytes(encode_module(mod))
    back = decode_binary(out.read_bytes())
    assert _normalize(module_to_dict(back)) == _normalize(module_to_dict(mod))
