from __future__ import annotations

from .base_backend import BaseBackend


class PicoGKBackend(BaseBackend):
    backend_id = "picogk"

    def to_mesh(self, model, spec):
        raise NotImplementedError("picogk backend stub: future LEAP71/PicoGK bridge")

    def repair_mesh(self, mesh):
        return mesh

    def validate_geometry(self, mesh, spec):
        return {"warning": "picogk backend stub"}
