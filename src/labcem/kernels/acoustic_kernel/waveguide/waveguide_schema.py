from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WaveguideSpec:
    family: str = "tritonia"
    throat_diameter: float = 50.0
    mouth_width: float = 200.0
    mouth_height: float = 140.0
    depth: float = 95.0
    coverage_h: Optional[float] = None
    coverage_v: Optional[float] = None
    segments: int = 96
    angular_segments: int = 144
    wall_thickness: float = 3.0
    flange_thickness: float = 4.0
    flange_margin: float = 12.0
    roundover_radius: float = 8.0
    throat_roundover: float = 3.0
    throat_adapter_depth: float = 8.0
    profile_power: float = 1.35
    morph_rate: float = 1.0

    @classmethod
    def from_dict(cls, spec: Dict[str, Any]) -> "WaveguideSpec":
        return cls(
            family=str(spec.get("family", "tritonia") or "tritonia").lower(),
            throat_diameter=float(spec.get("throat_diameter", 50.0)),
            mouth_width=float(spec.get("mouth_width", 200.0)),
            mouth_height=float(spec.get("mouth_height", 140.0)),
            depth=float(spec.get("depth", 95.0)),
            coverage_h=_to_optional_float(spec.get("coverage_h", spec.get("directivity_h"))),
            coverage_v=_to_optional_float(spec.get("coverage_v", spec.get("directivity_v"))),
            segments=max(24, int(spec.get("segments", 96))),
            angular_segments=max(32, int(spec.get("angular_segments", 144))),
            wall_thickness=max(0.8, float(spec.get("wall_thickness", 3.0))),
            flange_thickness=max(0.0, float(spec.get("flange_thickness", 4.0))),
            flange_margin=max(0.0, float(spec.get("flange_margin", 12.0))),
            roundover_radius=max(0.0, float(spec.get("roundover_radius", 8.0))),
            throat_roundover=max(0.0, float(spec.get("throat_roundover", 3.0))),
            throat_adapter_depth=max(0.0, float(spec.get("throat_adapter_depth", 8.0))),
            profile_power=max(0.4, float(spec.get("profile_power", 1.35))),
            morph_rate=max(0.4, float(spec.get("morph_rate", 1.0))),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family,
            "throat_diameter": self.throat_diameter,
            "mouth_width": self.mouth_width,
            "mouth_height": self.mouth_height,
            "depth": self.depth,
            "coverage_h": self.coverage_h,
            "coverage_v": self.coverage_v,
            "segments": self.segments,
            "angular_segments": self.angular_segments,
            "wall_thickness": self.wall_thickness,
            "flange_thickness": self.flange_thickness,
            "flange_margin": self.flange_margin,
            "roundover_radius": self.roundover_radius,
            "throat_roundover": self.throat_roundover,
            "throat_adapter_depth": self.throat_adapter_depth,
            "profile_power": self.profile_power,
            "morph_rate": self.morph_rate,
        }


def _to_optional_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None
