from __future__ import annotations

from typing import Dict

from ..backends.mesh_sdf_backend import MeshSDFBackend
from ..backends.openvdb_backend import OpenVDBBackend
from ..backends.picogk_backend import PicoGKBackend
from ..backends.python_sdf_backend import PythonSDFBackend


class BackendRegistry:
    def create(self, backend_id: str):
        key = (backend_id or "python_sdf").lower()
        if key == "python_sdf":
            return PythonSDFBackend()
        if key == "mesh_sdf":
            return MeshSDFBackend()
        if key == "picogk":
            return PicoGKBackend()
        if key == "openvdb":
            return OpenVDBBackend()
        raise ValueError(f"Unknown backend: {backend_id}")

    def list_backends(self):
        return ["python_sdf", "mesh_sdf", "picogk", "openvdb"]
