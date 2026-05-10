from __future__ import annotations

from .base_backend import BaseBackend


class MeshSDFBackend(BaseBackend):
    backend_id = "mesh_sdf"

    def to_mesh(self, model, spec):
        raise NotImplementedError("mesh_sdf backend stub: planned for mesh_to_sdf/pysdf integration")

    def repair_mesh(self, mesh):
        return mesh

    def validate_geometry(self, mesh, spec):
        return {"warning": "mesh_sdf backend stub"}
