from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class GeometryBackend(ABC):
    """Base contract for LabCEM geometry backends."""

    name: str = "base"

    @abstractmethod
    def create_waveguide(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def export_stl(self, mesh: Any, path: Path) -> Path:
        raise NotImplementedError
