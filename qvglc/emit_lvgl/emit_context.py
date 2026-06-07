from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from qvglc.profile import Profile, load_profile


@dataclass
class EmitContext:
    asset_root: Path | None = None
    profile: Profile | None = None
    extra_fonts: set[str] = field(default_factory=set)

    def resolve_profile(self, mod_profile: str) -> Profile:
        if self.profile is not None:
            return self.profile
        return load_profile(
            Path(__file__).resolve().parents[2] / "profiles" / f"{mod_profile}.yaml"
        )

    def resolve_asset(self, source: str) -> Path:
        if self.asset_root is None:
            raise FileNotFoundError("asset_root not set for Image emit")
        rel = source.lstrip("/")
        path = (self.asset_root / rel).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"image not found: {source} (resolved {path})")
        return path
