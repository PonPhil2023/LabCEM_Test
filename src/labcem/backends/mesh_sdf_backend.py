from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import trimesh

from .base_backend import GeometryBackend


class MeshSDFBackend(GeometryBackend):
    """Mesh-to-SDF backend placeholder with trimesh fallback."""

    name = "mesh_sdf"

    def create_waveguide(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        throat = float(spec["throat_diameter"])
        mouth_w = float(spec["mouth_width"])
        mouth_h = float(spec["mouth_height"])
        depth = float(spec["depth"])

        try:
            import mesh_to_sdf  # noqa: F401
            note = "mesh_to_sdf available; advanced conversion hook can be implemented here."
        except Exception:
            note = "mesh_to_sdf unavailable; using loft mesh placeholder."

        throat_mesh = trimesh.creation.cylinder(radius=throat * 0.5, height=max(depth * 0.2, 1.0), sections=64)
        mouth_mesh = trimesh.creation.box(extents=[mouth_w, mouth_h, max(depth * 0.1, 1.0)])
        mouth_mesh.apply_translation([0.0, 0.0, depth * 0.45])
        mesh = trimesh.util.concatenate([throat_mesh, mouth_mesh])

        return {"backend": self.name, "mesh": mesh, "notes": note}

    def export_stl(self, mesh: trimesh.Trimesh, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(path)
        return path
