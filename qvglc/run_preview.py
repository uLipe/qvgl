from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_preview_built(
    build_dir: Path,
    gen_dir: Path,
    lvgl_path: Path,
) -> Path:
    build_dir = build_dir.resolve()
    gen_dir = gen_dir.resolve()
    preview_bin = build_dir / "tests" / "preview" / "qvgl_preview"
    stamp = build_dir / ".qvgl_preview_stamp"
    key = f"{gen_dir}\n{lvgl_path.resolve()}\n"
    if preview_bin.is_file() and stamp.is_file() and stamp.read_text(encoding="utf-8") == key:
        return preview_bin

    build_dir.mkdir(parents=True, exist_ok=True)
    cmake = [
        "cmake",
        "-B",
        str(build_dir),
        "-S",
        str(_repo_root()),
        f"-DQVGL_LVGL_PATH={lvgl_path.resolve()}",
        f"-DQVGL_PREVIEW_GEN_DIR={gen_dir}",
        "-DQVGL_BUILD_TESTS=ON",
    ]
    r = subprocess.run(cmake, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmake configure failed:\n{r.stderr}")

    r = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "qvgl_preview", "-j"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"cmake build failed:\n{r.stderr}")

    if not preview_bin.is_file():
        raise RuntimeError(f"preview binary missing: {preview_bin}")

    stamp.write_text(key, encoding="utf-8")
    return preview_bin


def run_qml_preview(
    qml_path: Path,
    *,
    build_dir: Path | None = None,
    lvgl_path: Path | None = None,
    profile_path: Path | None = None,
    headless: bool = False,
    pressure: float | None = None,
    prop_sets: list[str] | None = None,
    loop_frames: int = 0,
    plot_animate: bool = False,
    exit_after: bool = False,
) -> int:
    from qvglc.emit_lvgl import emit_module
    from qvglc.lvgl_probe import probe_lvgl, resolve_lvgl_path
    from qvglc.parser import compile_qml, default_profile_path, load_profile

    root = _repo_root()
    build_dir = (build_dir or root / "build").resolve()
    lvgl_path = resolve_lvgl_path(lvgl_path, cwd=root).resolve()
    qml_path = qml_path.resolve()
    gen_dir = build_dir / "run" / qml_path.stem

    prof = load_profile(profile_path or default_profile_path())
    mod = compile_qml(qml_path, prof, module_name=qml_path.stem)
    caps = probe_lvgl(lvgl_path)
    emit_module(mod, caps, gen_dir, asset_root=qml_path.parent)

    sets: list[str] = list(prop_sets or [])

    preview_bin = ensure_preview_built(build_dir, gen_dir, lvgl_path)
    cmd = [str(preview_bin), "--gen-dir", str(gen_dir)]
    if headless:
        cmd.append("--headless")
    for item in sets:
        cmd.extend(["--set", item])
    if pressure is not None:
        cmd.extend(["--pressure", str(pressure)])
    if loop_frames:
        cmd.extend(["--loop-frames", str(loop_frames)])
    if plot_animate:
        cmd.append("--plot-animate")
    if exit_after:
        cmd.append("--exit")

    env = os.environ.copy()
    if headless and "SDL_VIDEODRIVER" not in env:
        env["SDL_VIDEODRIVER"] = "dummy"

    return subprocess.call(cmd, env=env)
