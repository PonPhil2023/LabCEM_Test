from __future__ import annotations
from typing import Any, Dict, List
from labcem.core.plugin.domain_kernel import DomainShapeKernel
from .components.midsole import MidsoleBuilder


class FootwearShapeKernel(DomainShapeKernel):
    kernel_name = "Footwear Shape Kernel"
    kernel_id = "footwear_kernel"
    version = "0.1.0"
    domain = "footwear"

    def __init__(self):
        self._builders = {"midsole": MidsoleBuilder()}

    def list_components(self) -> List[str]: return list(self._builders.keys())
    def get_component_builder(self, component_type: str): return self._builders.get(component_type, MidsoleBuilder())
    def validate_spec(self, spec: Dict[str, Any]) -> None: return None
    def validate_model(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]: return {"ok": True, "stub": True}
