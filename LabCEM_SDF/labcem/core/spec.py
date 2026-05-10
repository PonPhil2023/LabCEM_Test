from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DesignSpec:
    """Structured acoustic design spec used across layers."""

    type: str = "waveguide"
    throat_diameter: float = 25.0
    mouth_width: float = 180.0
    mouth_height: float = 120.0
    depth: float = 90.0
    directivity_h: float = 90.0
    directivity_v: float = 60.0
    bandwidth: Tuple[float, float] = (1000.0, 18000.0)
    wall_thickness: float = 3.0
    flange_thickness: float = 8.0
    resolution: float = 2.0
    meta: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "DesignSpec":
        return cls(**data)

    def to_dict(self) -> Dict:
        out = self.__dict__.copy()
        out["bandwidth"] = list(self.bandwidth)
        return out


@dataclass
class AcousticShape:
    """Geometry container exchanged by builders/backends/validators."""

    name: str
    mesh: object
    backend_name: str
    metadata: Dict = field(default_factory=dict)

    def stats(self) -> Dict:
        mesh = self.mesh
        return {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "volume_mm3": float(mesh.volume) if hasattr(mesh, "volume") else 0.0,
            "bounds_mm": mesh.bounds.tolist() if hasattr(mesh, "bounds") else None,
        }
