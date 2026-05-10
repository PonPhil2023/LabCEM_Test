from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import trimesh
from skimage.measure import marching_cubes

from .base_backend import GeometryBackend


class PythonSDFBackend(GeometryBackend):
    """Pure Python/Numpy MVP SDF backend."""

    name = "python_sdf"

    def create_waveguide(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        resolution = float(spec.get("resolution", 1.0) or 1.0)
        throat_d = float(spec["throat_diameter"])
        mouth_w = float(spec["mouth_width"])
        mouth_h = float(spec["mouth_height"])
        depth = float(spec["depth"])
        wall_t = float(spec.get("wall_thickness", 3.0) or 3.0)
        flange_t = float(spec.get("flange_thickness", 0.0) or 0.0)

        half_x = mouth_w * 0.5 + wall_t + 12.0
        half_y = mouth_h * 0.5 + wall_t + 12.0
        min_z = -max(flange_t, 0.0)
        max_z = depth + wall_t + 8.0

        xs = np.arange(-half_x, half_x + resolution, resolution, dtype=np.float32)
        ys = np.arange(-half_y, half_y + resolution, resolution, dtype=np.float32)
        zs = np.arange(min_z, max_z + resolution, resolution, dtype=np.float32)

        xx, yy, zz = np.meshgrid(xs, ys, zs, indexing="ij")
        inner = self._waveguide_channel(xx, yy, zz, throat_d, mouth_w, mouth_h, depth)
        outer = self._waveguide_channel(xx, yy, zz, throat_d + 2.0 * wall_t, mouth_w + 2.0 * wall_t, mouth_h + 2.0 * wall_t, depth)
        shell = np.maximum(outer, -inner)

        if flange_t > 0:
            flange_half_w = (mouth_w + 2.0 * wall_t) * 0.62
            flange_half_h = (mouth_h + 2.0 * wall_t) * 0.62
            flange = self._box_sdf(xx, yy, zz + flange_t * 0.5, flange_half_w, flange_half_h, flange_t * 0.5)
            throat_hole = np.sqrt(xx * xx + yy * yy) - (throat_d * 0.5)
            flange = np.maximum(flange, -throat_hole)
            shell = np.minimum(shell, flange)

        verts, faces, _normals, _vals = marching_cubes(shell.astype(np.float32), level=0.0, spacing=(resolution, resolution, resolution))
        verts[:, 0] += xs[0]
        verts[:, 1] += ys[0]
        verts[:, 2] += zs[0]

        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        return {
            "backend": self.name,
            "mesh": mesh,
            "sdf_grid": shell,
            "bbox": {"x": [float(xs[0]), float(xs[-1])], "y": [float(ys[0]), float(ys[-1])], "z": [float(zs[0]), float(zs[-1])]},
            "resolution": resolution,
        }

    def export_stl(self, mesh: trimesh.Trimesh, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(path)
        return path

    @staticmethod
    def _box_sdf(x: np.ndarray, y: np.ndarray, z: np.ndarray, hx: float, hy: float, hz: float) -> np.ndarray:
        qx = np.abs(x) - hx
        qy = np.abs(y) - hy
        qz = np.abs(z) - hz
        ax = np.maximum(qx, 0.0)
        ay = np.maximum(qy, 0.0)
        az = np.maximum(qz, 0.0)
        outside = np.sqrt(ax * ax + ay * ay + az * az)
        inside = np.minimum(np.maximum(np.maximum(qx, qy), qz), 0.0)
        return outside + inside

    @staticmethod
    def _waveguide_channel(x: np.ndarray, y: np.ndarray, z: np.ndarray, throat_d: float, mouth_w: float, mouth_h: float, depth: float) -> np.ndarray:
        zc = np.clip(z, 0.0, depth)
        t = zc / max(depth, 1e-6)

        a0 = throat_d * 0.5
        b0 = throat_d * 0.5
        a1 = mouth_w * 0.5
        b1 = mouth_h * 0.5

        smooth_t = t * t * (3.0 - 2.0 * t)
        a = a0 + (a1 - a0) * smooth_t
        b = b0 + (b1 - b0) * smooth_t

        p = 3.0
        q = (np.abs(x) / np.maximum(a, 1e-6)) ** p + (np.abs(y) / np.maximum(b, 1e-6)) ** p
        section = np.power(np.maximum(q, 0.0), 1.0 / p) - 1.0

        before = -z
        after = z - depth
        z_cap = np.maximum(before, after)
        return np.maximum(section * np.minimum(a, b), z_cap)
