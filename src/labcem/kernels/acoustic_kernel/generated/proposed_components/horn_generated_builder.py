# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from typing import Any, Dict

from labcem.core.plugin.component_builder import ComponentBuilder


class HornGeneratedBuilder(ComponentBuilder):
    component_type = "horn"
    display_name = "Horn"
    domain = "acoustic"

    def get_schema(self) -> Dict[str, Any]:
        return {'kernel_id': 'acoustic_kernel',
 'domain': 'acoustic',
 'component_type': 'horn',
 'display_name': 'Horn',
 'aliases': ['horn'],
 'parameters': {},
 'generated_from': ['D:\\Code\\CEM_Test\\src\\labcem\\kernels\\acoustic_kernel\\knowledge\\cards\\multi_ATH_-_Advanced-Transition_Horns_ATH_-_Segmentizing_a_horn_Ath-AP1_horn_card_001.json'],
 'created_at': '2026-05-10T14:27:37.781773Z'}

    def solve_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(spec)
        out.setdefault("component_type", self.component_type)
        for name, cfg in self.get_schema().get("parameters", {}).items():
            if isinstance(cfg, dict) and "default" in cfg:
                out.setdefault(name, cfg.get("default"))
        return out

    def build(self, spec: Dict[str, Any], backend: Any):
        return backend.build_waveguide_sdf(spec)

    def validate(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "errors": []}

    def metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "display_name": self.display_name,
            "domain": self.domain,
            "generated": True,
        }
