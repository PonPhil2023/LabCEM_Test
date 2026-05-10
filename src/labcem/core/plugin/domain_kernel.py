from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DomainShapeKernel(ABC):
    kernel_name: str = ""
    kernel_id: str = ""
    version: str = "0.1.0"
    domain: str = "general"

    @abstractmethod
    def list_components(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_component_builder(self, component_type: str):
        raise NotImplementedError

    @abstractmethod
    def validate_spec(self, spec: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def validate_model(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def get_default_materials(self) -> List[Dict[str, Any]]:
        return []

    def get_manufacturing_rules(self) -> Dict[str, Any]:
        return {}

    def export_metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "kernel_id": self.kernel_id,
            "kernel_name": self.kernel_name,
            "version": self.version,
            "domain": self.domain,
            "component_type": spec.get("component_type", "unknown"),
        }
