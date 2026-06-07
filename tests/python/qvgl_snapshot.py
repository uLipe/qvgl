from __future__ import annotations

import os
import subprocess
from pathlib import Path

from qvglc.run_preview import ensure_preview_built


def build_preview(
    build_dir: Path,
    gen_dir: Path,
    lvgl_path: Path,
) -> Path:
    return ensure_preview_built(build_dir, gen_dir.resolve(), lvgl_path.resolve())


def dump_preview_frame(
    preview_bin: Path,
    gen_dir: Path,
    out_png: Path,
    *,
    prop_sets: list[str] | None = None,
    frames: int = 5,
    cwd: Path | None = None,
) -> None:
    cmd = [
        str(preview_bin),
        "--gen-dir",
        str(gen_dir.resolve()),
        "--headless",
        "--frames",
        str(frames),
        "--dump-fb",
        str(out_png),
    ]
    for item in prop_sets or []:
        cmd.extend(["--set", item])

    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"qvgl_preview failed: {r.stderr or r.stdout}")
    if not out_png.is_file():
        raise RuntimeError(f"preview dump missing: {out_png}")
