from __future__ import annotations

from typing import Any, Dict

from labcem.backends.base_backend import GeometryBackend
from labcem.backends.mesh_sdf_backend import MeshSDFBackend
from labcem.backends.picogk_backend import PicoGKBackend
from labcem.backends.python_sdf_backend import PythonSDFBackend


REQUIRED_FIELDS = ["type", "throat_diameter", "mouth_width", "mouth_height", "depth"]


def _backend_from_name(name: str) -> GeometryBackend:
    key = (name or "python_sdf").strip().lower()
    if key == "mesh_sdf":
        return MeshSDFBackend()
    if key == "picogk":
        return PicoGKBackend()
    return PythonSDFBackend()


def create_waveguide(spec: Dict[str, Any]) -> Dict[str, Any]:
    for field in REQUIRED_FIELDS:
        if field not in spec:
            raise ValueError("Missing required field: {0}".format(field))
    if str(spec.get("type", "")).lower() != "waveguide":
        raise ValueError("spec.type must be 'waveguide'")

    backend = _backend_from_name(str(spec.get("backend", "python_sdf")))
    result = backend.create_waveguide(spec)
    result["spec"] = dict(spec)
    result["backend_obj"] = backend
    return result
