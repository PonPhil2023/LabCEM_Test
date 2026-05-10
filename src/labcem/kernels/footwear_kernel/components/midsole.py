from __future__ import annotations
from typing import Any, Dict
from labcem.core.plugin.component_builder import ComponentBuilder


class MidsoleBuilder(ComponentBuilder):
    component_type = "midsole"
    display_name = "Midsole"
    domain = "footwear"

    def get_schema(self) -> Dict[str, Any]: return {"type": "object"}
    def solve_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]: return {**spec, "component_type": self.component_type}
    def build(self, spec: Dict[str, Any], backend: Any): return backend.build_waveguide_sdf(spec)
    def validate(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]: return {"ok": True, "stub": True}
    def metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]: return {"component_type": self.component_type, "stub": True}
