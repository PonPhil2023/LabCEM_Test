from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import trimesh

from ..core.spec import AcousticShape, DesignSpec


@dataclass
class GeometryValidator:
    min_wall_thickness_mm: float = 2.0

    def validate(self, shape: AcousticShape, spec: DesignSpec) -> Dict:
        mesh: trimesh.Trimesh = shape.mesh
        extents = mesh.extents if mesh.extents is not None else np.array([0.0, 0.0, 0.0])
        checks = {
            "watertight": bool(mesh.is_watertight),
            "volume_positive": bool(abs(mesh.volume) > 0),
            "throat_mouth_alignment": bool(spec.mouth_width > spec.throat_diameter and spec.mouth_height > spec.throat_diameter),
            "air_path_depth_positive": bool(spec.depth > 0),
            "wall_thickness_ok": bool(spec.wall_thickness >= self.min_wall_thickness_mm),
            "self_intersection_risk": bool(not mesh.is_winding_consistent),
            "printability_basic": bool(np.min(extents) > 0.5),
        }
        return {
            "ok": bool(all([checks["volume_positive"], checks["wall_thickness_ok"], checks["air_path_depth_positive"], checks["throat_mouth_alignment"]])),
            "backend": shape.backend_name,
            "checks": checks,
            "mesh_stats": shape.stats(),
            "spec": spec.to_dict(),
        }


def validate_geometry(shape: AcousticShape, spec: Dict) -> Dict:
    return GeometryValidator().validate(shape, DesignSpec.from_dict(spec))
