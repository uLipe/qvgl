from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from qvglc.emit_lvgl import emit_module
from qvglc.lvgl_probe import probe_lvgl
from qvglc.parser import compile_qml, load_profile
from qvgl_snapshot import build_preview, dump_preview_frame

ROOT = Path(__file__).resolve().parents[2]
QT_PARITY_MANIFEST = ROOT / "examples/conformance/qt_parity.yaml"


def load_qt_parity_cases() -> list[dict]:
    data = yaml.safe_load(QT_PARITY_MANIFEST.read_text(encoding="utf-8"))
    return data["cases"]


def viewport_size(qml_path: Path, profile_path: Path) -> tuple[int, int]:
    profile = load_profile(profile_path)
    mod = compile_qml(qml_path, profile, module_name=qml_path.stem)
    root = mod.nodes[mod.root]
    w = int(root.properties.get("width", profile.display_width))
    h = int(root.properties.get("height", profile.display_height))
    return w, h


def render_qt_snapshot(
    qml_path: Path,
    width: int,
    height: int,
    out_png: Path,
    *,
    settle_ms: int = 400,
) -> None:
    from PyQt6.QtCore import QEventLoop, QSize, QTimer, QUrl
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQuick import QQuickView

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv)

    view = QQuickView()
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(qml_path.resolve())))
    if view.status() == QQuickView.Status.Error:
        errs = [e.toString() for e in view.errors()]
        raise RuntimeError(f"Qt QML load failed: {errs}")

    view.resize(QSize(width, height))
    view.show()

    loop = QEventLoop()
    QTimer.singleShot(settle_ms, loop.quit)
    loop.exec()

    img = view.grabWindow()
    if img.isNull():
        raise RuntimeError("Qt grabWindow returned null image")

    out_png.parent.mkdir(parents=True, exist_ok=True)
    if not img.save(str(out_png)):
        raise RuntimeError(f"Qt failed to write {out_png}")


def render_qvgl_snapshot(
    qml_path: Path,
    profile_path: Path,
    out_png: Path,
    *,
    build_dir: Path,
    lvgl_path: Path,
    prop_sets: list[str] | None = None,
    frames: int = 5,
) -> None:
    profile = load_profile(profile_path)
    mod = compile_qml(qml_path, profile, module_name=qml_path.stem)
    caps = probe_lvgl(lvgl_path)
    gen_dir = build_dir / f"gen_{qml_path.stem}"
    emit_module(mod, caps, gen_dir, asset_root=qml_path.parent)

    preview = build_preview(build_dir, gen_dir.resolve(), lvgl_path)
    dump_preview_frame(
        preview,
        gen_dir.resolve(),
        out_png,
        prop_sets=prop_sets,
        frames=frames,
        cwd=ROOT,
    )
