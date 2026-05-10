from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import numpy as np
import trimesh
from skimage import measure

from .spec import AcousticShape, DesignSpec


class SDFBackend(ABC):
    """Backend interface for creating shapes from design specs."""

    name: str = "base"

    @abstractmethod
    def create_waveguide(self, spec: DesignSpec) -> AcousticShape:
        raise NotImplementedError


@dataclass
class PythonSDFBackend(SDFBackend):
    """MVP backend: numpy SDF grid + marching cubes."""

    name: str = "python_sdf"

    def create_waveguide(self, spec: DesignSpec) -> AcousticShape:
        mesh = _build_waveguide_mesh_with_sdf(spec)
        return AcousticShape(name="waveguide", mesh=mesh, backend_name=self.name, metadata=spec.to_dict())


@dataclass
class MeshToSDFBackend(SDFBackend):
    """Stage-2 placeholder for mesh_to_sdf / pysdf pipeline."""

    name: str = "mesh_to_sdf"

    def create_waveguide(self, spec: DesignSpec) -> AcousticShape:
        return PythonSDFBackend().create_waveguide(spec)


@dataclass
class PicoGKBackend(SDFBackend):
    """Stage-3 placeholder for PicoGK runtime binding."""

    name: str = "picogk"

    def create_waveguide(self, spec: DesignSpec) -> AcousticShape:
        return PythonSDFBackend().create_waveguide(spec)


@dataclass
class OpenVDBBackend(SDFBackend):
    """Stage-3 placeholder for OpenVDB pipeline."""

    name: str = "openvdb"

    def create_waveguide(self, spec: DesignSpec) -> AcousticShape:
        return PythonSDFBackend().create_waveguide(spec)


def _build_waveguide_mesh_with_sdf(spec: DesignSpec) -> trimesh.Trimesh:
    throat_r = spec.throat_diameter * 0.5
    mouth_rx = spec.mouth_width * 0.5
    mouth_ry = spec.mouth_height * 0.5
    depth = spec.depth
    wall = spec.wall_thickness
    flange = spec.flange_thickness
    res = max(1.0, spec.resolution)

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

    flange_outer = np.maximum(np.maximum(np.abs(X) - (mouth_rx + wall + flange), np.abs(Y) - (mouth_ry + wall + flange)), np.abs(Z - depth) - flange)
    mouth_cut = np.maximum(np.sqrt((X / (mouth_rx + wall)) ** 2 + (Y / (mouth_ry + wall)) ** 2) - 1.0, Z - (depth + flange))
    back_plate = np.maximum(flange_outer, -mouth_cut)

    sdf = np.minimum(waveguide, back_plate)

    verts, faces, _, _ = measure.marching_cubes(sdf, level=0.0, spacing=(res, res, res))
    verts[:, 0] += x_min
    verts[:, 1] += y_min
    verts[:, 2] += z_min

    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    if not mesh.is_watertight:
        mesh.fill_holes()
    mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()
    mesh.rezero()
    return mesh


def backend_factory(name: str) -> SDFBackend:
    registry: Dict[str, SDFBackend] = {
        "python_sdf": PythonSDFBackend(),
        "mesh_to_sdf": MeshToSDFBackend(),
        "picogk": PicoGKBackend(),
        "openvdb": OpenVDBBackend(),
    }
    if name not in registry:
        raise ValueError(f"Unknown backend: {name}")
    return registry[name]
