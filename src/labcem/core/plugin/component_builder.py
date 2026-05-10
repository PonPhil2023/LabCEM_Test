from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ComponentBuilder(ABC):
    component_type: str = ""
    display_name: str = ""
    domain: str = "general"

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def solve_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build(self, spec: Dict[str, Any], backend: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def validate(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
