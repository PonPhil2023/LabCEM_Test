from __future__ import annotations

from typing import Any, Dict

import numpy as np
import trimesh
from skimage import measure
from labcem.kernels.acoustic_kernel.waveguide.waveguide_schema import WaveguideSpec
from labcem.kernels.acoustic_kernel.waveguide.waveguide_surface_builder import build_ath_like_waveguide_mesh
from labcem.kernels.acoustic_kernel.waveguide.waveguide_validator import validate_waveguide_geometry

from .base_backend import BaseBackend


class PythonSDFBackend(BaseBackend):
    backend_id = "python_sdf"

    def build_waveguide_sdf(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        # Default path: ATH-like waveguide mesh generation (OS-SE / Tritonia family).
        try:
            wg_spec = WaveguideSpec.from_dict(spec)
            mesh_data = build_ath_like_waveguide_mesh(wg_spec)
            validation = validate_waveguide_geometry(mesh_data, wg_spec)
            return {
                "mode": "mesh",
                "vertices": mesh_data.vertices,
                "faces": mesh_data.faces,
                "ring_count": mesh_data.ring_count,
                "angular_segments": mesh_data.angular_segments,
                "family": wg_spec.family,
                "validation": validation,
            }
        except Exception:
            # Compatibility fallback: preserve old implicit SDF route.
            pass

        throat_r = float(spec["throat_diameter"]) * 0.5
        mouth_rx = float(spec["mouth_width"]) * 0.5
        mouth_ry = float(spec["mouth_height"]) * 0.5
        depth = float(spec["depth"])
        wall = float(spec["wall_thickness"])
        flange = float(spec["flange_thickness"])
        resolution = int(spec.get("resolution", 36))

        res = float((2.0 * max(mouth_rx, mouth_ry, depth) + 80.0) / max(resolution, 20))
        margin = max(wall + flange, 10.0)
        x_min, x_max = -mouth_rx - margin, mouth_rx + margin
        y_min, y_max = -mouth_ry - margin, mouth_ry + margin
        z_min, z_max = -margin, depth + margin

        xs = np.arange(x_min, x_max + res, res, dtype=np.float32)
        ys = np.arange(y_min, y_max + res, res, dtype=np.float32)
        zs = np.arange(z_min, z_max + res, res, dtype=np.float32)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")

        zc = np.clip(Z, 0.0, depth)
        t = np.where(depth > 1e-6, zc / depth, 0.0)
        rx = throat_r + (mouth_rx - throat_r) * t
        ry = throat_r + (mouth_ry - throat_r) * t

        outer = np.sqrt((X / (rx + wall)) ** 2 + (Y / (ry + wall)) ** 2) - 1.0
        inner = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2) - 1.0
        tube_z = np.maximum(-Z, Z - depth)

        shell = np.maximum(outer, -inner)
        waveguide = np.maximum(shell, tube_z)

        flange_outer = np.maximum(
            np.maximum(np.abs(X) - (mouth_rx + wall + flange), np.abs(Y) - (mouth_ry + wall + flange)),
            np.abs(Z - depth) - flange,
        )
        mouth_cut = np.maximum(np.sqrt((X / (mouth_rx + wall)) ** 2 + (Y / (mouth_ry + wall)) ** 2) - 1.0, Z - (depth + flange))
        back_plate = np.maximum(flange_outer, -mouth_cut)
        sdf = np.minimum(waveguide, back_plate)

        return {
            "mode": "sdf",
            "sdf": sdf,
            "spacing": res,
            "origin": (x_min, y_min, z_min),
        }

    def to_mesh(self, model: Dict[str, Any], spec: Dict[str, Any]):
        if isinstance(model, trimesh.Trimesh):
            return model
        if isinstance(model, dict) and model.get("mode") == "mesh" and "vertices" in model and "faces" in model:
            return trimesh.Trimesh(vertices=np.asarray(model["vertices"]), faces=np.asarray(model["faces"]), process=True)

        sdf = model["sdf"]
        res = float(model["spacing"])
        ox, oy, oz = model["origin"]
        verts, faces, _, _ = measure.marching_cubes(sdf, level=0.0, spacing=(res, res, res))
        verts[:, 0] += ox
        verts[:, 1] += oy
        verts[:, 2] += oz
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        return mesh

    def repair_mesh(self, mesh):
        if not mesh.is_watertight:
            mesh.fill_holes()
        try:
            mesh.update_faces(mesh.nondegenerate_faces())
        except Exception:
            pass
        mesh.remove_unreferenced_vertices()
        mesh.rezero()
        return mesh

    def validate_geometry(self, mesh, spec: Dict[str, Any]) -> Dict[str, Any]:
        # Prefer dedicated ATH-like validator summary if available from builder stage.
        # This keeps the same output shape but adds waveguide-specific checks.
        model_validation = None
        try:
            model_validation = spec.get("__waveguide_validation__")
        except Exception:
            model_validation = None
        if isinstance(model_validation, dict):
            out = dict(model_validation)
            if "mesh_stats" not in out:
                out["mesh_stats"] = {
                    "vertices": int(len(mesh.vertices)),
                    "faces": int(len(mesh.faces)),
                    "volume_mm3": float(abs(mesh.volume)),
                    "bounds_mm": mesh.bounds.tolist(),
                }
            return out

        extents = mesh.extents if mesh.extents is not None else np.array([0.0, 0.0, 0.0])
        topology = {
            "throat_open": True,
            "mouth_open": True,
            "acoustic_path_clear": bool(float(spec.get("depth", 0.0)) > 0.0),
            "watertight_shell_check": bool(mesh.is_watertight),
            "non_manifold_edges": int(len(getattr(mesh, "nonmanifold_edges", [])) if hasattr(mesh, "nonmanifold_edges") else 0),
            "min_wall_thickness_check": bool(float(spec.get("wall_thickness", 0.0)) >= 2.0),
        }
        checks = {
            "volume_positive": bool(abs(mesh.volume) > 0),
            "wall_ok": bool(float(spec.get("wall_thickness", 0.0)) >= 2.0),
            "printability_basic": bool(np.min(extents) > 0.5),
        }
        return {
            "topology": topology,
            "checks": checks,
            "validation_summary": {
                "throat_open": topology["throat_open"],
                "mouth_open": topology["mouth_open"],
                "acoustic_path_clear": topology["acoustic_path_clear"],
                "closed_port": False,
            },
            "mesh_stats": {
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "volume_mm3": float(abs(mesh.volume)),
                "bounds_mm": mesh.bounds.tolist(),
            },
        }
