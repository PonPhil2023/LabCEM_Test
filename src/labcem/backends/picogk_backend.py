from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .base_backend import GeometryBackend


class PicoGKBackend(GeometryBackend):
    """Stub backend for future LEAP71/PicoGK integration."""

    name = "picogk"

    def __init__(self, runtime_path: str | None = None) -> None:
        self.runtime_path = runtime_path

    def create_waveguide(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "backend": self.name,
            "status": "stub",
            "message": "PicoGK backend is not wired yet. Use python_sdf backend for MVP.",
            "spec": spec,
        }

    def export_stl(self, mesh: Any, path: Path) -> Path:
        raise NotImplementedError("PicoGK backend stub cannot export STL yet.")
