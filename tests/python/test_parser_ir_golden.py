from __future__ import annotations

import json
from pathlib import Path

import subprocess

from qvglc.ir import load_json_path, module_to_dict, validate
from qvglc.parser import compile_qml, default_profile_path, load_profile, parse_qml
from qvglc.parser.ir_builder import build_ir
from qvglc.parser.sema import analyze

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_JSON = ROOT / "examples/turbo_gauge/golden/turbo_gauge.qvglir.json"
QML = ROOT / "examples/turbo_gauge/turbo_gauge.qml"


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


def test_turbo_gauge_qml_matches_golden_ir():
    prof = load_profile(default_profile_path())
    src = QML.read_text(encoding="utf-8")
    doc = parse_qml(src)
    analyze(doc, prof)
    mod = build_ir(doc, prof, "turbo_gauge")
    validate(mod)

    golden = load_json_path(GOLDEN_JSON)
    assert _normalize(module_to_dict(mod)) == _normalize(module_to_dict(golden))


def test_compile_qml_cli(tmp_path: Path):
    out = tmp_path / "gen"
    ir_out = tmp_path / "turbo_gauge.qvglir"
    proc = subprocess.run(
        ["qvglc", "compile", str(QML), "-o", str(out), "--ir-out", str(ir_out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert ir_out.is_file()
    assert (out / "ui_turbo_gauge.c").is_file()
