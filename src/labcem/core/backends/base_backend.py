from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseBackend(ABC):
    backend_id: str = "base"

    @abstractmethod
    def to_mesh(self, model: Any, spec: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def repair_mesh(self, mesh):
        raise NotImplementedError

    @abstractmethod
    def validate_geometry(self, mesh, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
