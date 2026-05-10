from __future__ import annotations

from .base_backend import BaseBackend


class OpenVDBBackend(BaseBackend):
    backend_id = "openvdb"

    def to_mesh(self, model, spec):
        raise NotImplementedError("openvdb backend stub: future OpenVDB bridge")

    def repair_mesh(self, mesh):
        return mesh

    def validate_geometry(self, mesh, spec):
        return {"warning": "openvdb backend stub"}
