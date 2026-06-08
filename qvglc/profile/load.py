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


def load_profile(path: Path | str) -> Profile:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
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


def default_profile_path() -> Path:
    return Path(__file__).resolve().parents[2] / "profiles" / "ultralite_v1.yaml"
