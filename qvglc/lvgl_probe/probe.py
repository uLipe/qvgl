from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


class LvglProbeError(Exception):
    pass


@dataclass
class LvglCapabilities:
    lvgl_path: Path
    major: int = 0
    minor: int = 0
    patch: int = 0
    version_info: str = ""
    features: dict[str, int] = field(default_factory=dict)

    @property
    def version_string(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        info = self.version_info.strip().strip('"')
        if info:
            return f"{base}-{info}"
        return base

    def require(self, name: str, hint: str = "") -> None:
        if self.features.get(name, 0) != 1:
            msg = f"LVGL at {self.lvgl_path} requires {name}=1"
            if hint:
                msg += f" ({hint})"
            raise LvglProbeError(msg)

    def require_arc_gauge(self) -> None:
        self.require("LV_USE_ARC", "enable CONFIG_LV_USE_ARC in sdkconfig")
        self.require("LV_USE_LABEL", "enable CONFIG_LV_USE_LABEL")


_VERSION_RE = re.compile(
    r"#define\s+LVGL_VERSION_(MAJOR|MINOR|PATCH|INFO)\s+(.+)"
)
_DEFINE_RE = re.compile(r"#define\s+(LV_[A-Z0-9_]+)\s+(\d+)")


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise LvglProbeError(f"missing file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_version(text: str) -> tuple[int, int, int, str]:
    vals: dict[str, str] = {}
    for m in _VERSION_RE.finditer(text):
        vals[m.group(1)] = m.group(2).strip()
    try:
        major = int(vals["MAJOR"])
        minor = int(vals["MINOR"])
        patch = int(vals["PATCH"])
    except KeyError as e:
        raise LvglProbeError("lv_version.h: missing version macros") from e
    info = vals.get("INFO", '""').strip()
    if info.startswith('"') and info.endswith('"'):
        info = info[1:-1]
    return major, minor, patch, info


def _parse_features(text: str, names: set[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for m in _DEFINE_RE.finditer(text):
        name = m.group(1)
        if name in names:
            out[name] = int(m.group(2))
    return out


_PROBE_FEATURES = {
    "LV_USE_ARC",
    "LV_USE_SCALE",
    "LV_USE_LABEL",
    "LV_USE_SLIDER",
    "LV_USE_SWITCH",
    "LV_USE_CHECKBOX",
    "LV_USE_FLOAT",
    "LV_FONT_MONTSERRAT_14",
    "LV_FONT_MONTSERRAT_36",
}


def probe_lvgl(lvgl_path: Path) -> LvglCapabilities:
    root = lvgl_path.resolve()
    if not root.is_dir():
        raise LvglProbeError(f"not a directory: {root}")

    ver_paths = [
        root / "include/lvgl/lv_version.h",
        root / "lv_version.h",
    ]
    ver_text = ""
    for p in ver_paths:
        if p.is_file():
            ver_text = _read_text(p)
            break
    if not ver_text:
        raise LvglProbeError(f"lv_version.h not found under {root}")

    major, minor, patch, info = _parse_version(ver_text)

    conf_paths = [
        root / "lv_conf.h",
        root / "lv_conf_template.h",
        root / "include/lv_conf.h",
    ]
    conf_text = ""
    for p in conf_paths:
        if p.is_file():
            conf_text = _read_text(p)
            break
    if not conf_text:
        raise LvglProbeError(f"lv_conf.h / lv_conf_template.h not found under {root}")

    features = _parse_features(conf_text, _PROBE_FEATURES)
    for name in _PROBE_FEATURES:
        features.setdefault(name, 0)

    return LvglCapabilities(
        lvgl_path=root,
        major=major,
        minor=minor,
        patch=patch,
        version_info=info,
        features=features,
    )
