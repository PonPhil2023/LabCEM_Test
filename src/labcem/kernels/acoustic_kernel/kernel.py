from __future__ import annotations

from typing import Any, Dict, List

from labcem.core.plugin.domain_kernel import DomainShapeKernel

from .components.cavity import CavityBuilder
from .components.diffuser import DiffuserBuilder
from .components.horn import HornBuilder
from .components.port import PortBuilder
from .components.waveguide import WaveguideBuilder


class AcousticShapeKernel(DomainShapeKernel):
    kernel_name = "Acoustic Shape Kernel"
    kernel_id = "acoustic_kernel"
    version = "0.1.0"
    domain = "acoustic"

    def __init__(self):
        self._builders = {
            "waveguide": WaveguideBuilder(),
            "horn": HornBuilder(),
            "diffuser": DiffuserBuilder(),
            "cavity": CavityBuilder(),
            "port": PortBuilder(),
        }

    def list_components(self) -> List[str]:
        return list(self._builders.keys())

    def get_component_builder(self, component_type: str):
        c = (component_type or "waveguide").lower()
        if c not in self._builders:
            raise ValueError(f"Unsupported acoustic component: {component_type}")
        return self._builders[c]

    def validate_spec(self, spec: Dict[str, Any]) -> None:
        if spec.get("component_type", "waveguide") not in self._builders:
            raise ValueError("component_type is invalid for acoustic kernel")

    def validate_model(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "kernel": self.kernel_id}

    def get_default_materials(self):
        return [
            {"name": "PLA", "density_g_cm3": 1.24},
            {"name": "PETG", "density_g_cm3": 1.27},
        ]

    def get_manufacturing_rules(self):
        return {"min_wall_thickness_mm": 2.0, "preferred_nozzle_mm": 0.4}
