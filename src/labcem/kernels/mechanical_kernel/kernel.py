from __future__ import annotations
from typing import Any, Dict, List
from labcem.core.plugin.domain_kernel import DomainShapeKernel
from .components.bracket import BracketBuilder


class MechanicalShapeKernel(DomainShapeKernel):
    kernel_name = "Mechanical Shape Kernel"
    kernel_id = "mechanical_kernel"
    version = "0.1.0"
    domain = "mechanical"

    def __init__(self):
        self._builders = {"bracket": BracketBuilder()}

    def list_components(self) -> List[str]: return list(self._builders.keys())
    def get_component_builder(self, component_type: str): return self._builders.get(component_type, BracketBuilder())
    def validate_spec(self, spec: Dict[str, Any]) -> None: return None
    def validate_model(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]: return {"ok": True, "stub": True}
