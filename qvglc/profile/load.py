from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FontTier:
    max_pixel_size: int
    lv_id: str


DEFAULT_FONT_TIERS: tuple[FontTier, ...] = (
    FontTier(14, "montserrat_14"),
    FontTier(36, "montserrat_36"),
    FontTier(9999, "montserrat_48"),
)


@dataclass
class Profile:
    name: str
    version: int
    allowed_imports: list[str]
    types: dict[str, dict]
    allowed_anchors: list[str]
    allowed_exprs: list[str]
    disallow_exprs: list[str]
    allowed_animations: list[str]
    display_width: int = 400
    display_height: int = 400
    fail_on_unknown_type: bool = True
    fail_on_unknown_property: bool = True
    font_tiers: tuple[FontTier, ...] = DEFAULT_FONT_TIERS
    theme_colors: dict[str, str] = field(default_factory=dict)

    def font_for_pixel_size(self, pixel_size: int) -> str:
        for tier in self.font_tiers:
            if pixel_size <= tier.max_pixel_size:
                return tier.lv_id
        return self.font_tiers[-1].lv_id

    def type_names(self) -> set[str]:
        return set(self.types.keys())

    def properties_for(self, type_name: str) -> set[str]:
        t = self.types.get(type_name, {})
        props = set(t.get("properties", []))
        base = t.get("extends")
        if base and base in self.types:
            props |= self.properties_for(base)
        return props

    def signals_for(self, type_name: str) -> set[str]:
        t = self.types.get(type_name, {})
        sigs = set(t.get("signals", []))
        base = t.get("extends")
        if base and base in self.types:
            sigs |= self.signals_for(base)
        return sigs


def _deep_merge_dict(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, val in override.items():
        if key == "extends":
            continue
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge_dict(out[key], val)
        else:
            out[key] = val
    return out


def load_profile(path: Path | str) -> Profile:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    extends = data.get("extends")
    if extends:
        base_path = Path(extends)
        if not base_path.is_absolute():
            base_path = p.parent / base_path
        base_data = yaml.safe_load(base_path.read_text(encoding="utf-8"))
        data = _deep_merge_dict(base_data, data)
    cov = data.get("coverage", {})
    bindings = data.get("bindings", {})
    display = data.get("display", {})
    fonts_section = data.get("fonts", {})
    tiers_raw = fonts_section.get("tiers")
    if tiers_raw:
        font_tiers = tuple(
            FontTier(int(t["max_pixel_size"]), str(t["lv_id"])) for t in tiers_raw
        )
    else:
        font_tiers = DEFAULT_FONT_TIERS
    theme_section = data.get("theme", {})
    theme_colors = dict(theme_section.get("colors", {}))
    aliases = theme_section.get("aliases", {})
    if aliases:
        from qvglc.theme import merge_theme_aliases

        theme_colors = merge_theme_aliases(theme_colors, dict(aliases))
    return Profile(
        name=str(data["name"]),
        version=int(data.get("version", 1)),
        allowed_imports=list(data.get("imports", {}).get("allowed", [])),
        types=dict(data.get("types", {})),
        allowed_anchors=list(data.get("anchors", {}).get("allowed", [])),
        allowed_exprs=list(bindings.get("allowed_exprs", [])),
        disallow_exprs=list(bindings.get("disallow", [])),
        allowed_animations=list(data.get("animations", {}).get("allowed", [])),
        display_width=int(display.get("width", 400)),
        display_height=int(display.get("height", 400)),
        fail_on_unknown_type=bool(cov.get("fail_on_unknown_type", True)),
        fail_on_unknown_property=bool(cov.get("fail_on_unknown_property", True)),
        font_tiers=font_tiers,
        theme_colors=theme_colors,
    )


def apply_display_override(profile: Profile, width: int | None, height: int | None) -> Profile:
    if width is None and height is None:
        return profile
    profile.display_width = int(width) if width is not None else profile.display_width
    profile.display_height = int(height) if height is not None else profile.display_height
    return profile


def apply_mcu_root_display(mod, profile: Profile) -> None:
    root = mod.nodes[mod.root]
    root.properties["width"] = profile.display_width
    root.properties["height"] = profile.display_height


def default_profile_path() -> Path:
    return Path(__file__).resolve().parents[2] / "profiles" / "ultralite_v1.yaml"
