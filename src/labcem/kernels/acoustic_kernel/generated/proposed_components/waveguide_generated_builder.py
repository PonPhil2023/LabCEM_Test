# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from typing import Any, Dict

from labcem.core.plugin.component_builder import ComponentBuilder


class WaveguideGeneratedBuilder(ComponentBuilder):
    component_type = "waveguide"
    display_name = "Waveguide"
    domain = "acoustic"

    def get_schema(self) -> Dict[str, Any]:
        return {'kernel_id': 'acoustic_kernel',
 'domain': 'acoustic',
 'component_type': 'waveguide',
 'display_name': 'Waveguide',
 'aliases': ['waveguide', '波導', '號角導波器'],
 'parameters': {'throat_diameter': {'type': 'float',
                                    'unit': 'mm',
                                    'required': True,
                                    'default': 25.0,
                                    'aliases': ['throat', 'throat diameter', '喉口', '入口', '入口直徑']},
                'mouth_width': {'type': 'float',
                                'unit': 'mm',
                                'required': True,
                                'default': 180.0,
                                'aliases': ['mouth width', '出口寬度', '出口寬', 'mouth_w']},
                'mouth_height': {'type': 'float',
                                 'unit': 'mm',
                                 'required': True,
                                 'default': 120.0,
                                 'aliases': ['mouth height', '出口高度', '出口高', 'mouth_h']},
                'depth': {'type': 'float',
                          'unit': 'mm',
                          'required': True,
                          'default': 90.0,
                          'aliases': ['depth', 'length', '深度', '波導深度']},
                'directivity_h': {'type': 'float',
                                  'unit': 'deg',
                                  'required': False,
                                  'default': 90.0,
                                  'aliases': ['horizontal directivity', '水平指向性', '水平覆蓋角']},
                'directivity_v': {'type': 'float',
                                  'unit': 'deg',
                                  'required': False,
                                  'default': 60.0,
                                  'aliases': ['vertical directivity', '垂直指向性', '垂直覆蓋角']},
                'wall_thickness': {'type': 'float',
                                   'unit': 'mm',
                                   'required': False,
                                   'default': 3.0,
                                   'aliases': ['wall thickness', '壁厚']},
                'flange_thickness': {'type': 'float',
                                     'unit': 'mm',
                                     'required': False,
                                     'default': 8.0,
                                     'aliases': ['flange', 'flange thickness', '法蘭', '法蘭厚度']},
                'flare_profile': {'type': 'enum',
                                  'unit': '-',
                                  'required': False,
                                  'default': 'superellipse',
                                  'choices': ['linear',
                                              'superellipse',
                                              'exponential',
                                              'tractrix',
                                              'conical'],
                                  'aliases': ['flare', 'profile', 'curve', '曲線', '擴張曲線']},
                'resolution': {'type': 'float',
                               'unit': 'mm',
                               'required': False,
                               'default': 1.0,
                               'aliases': ['resolution', '解析度']}},
 'generated_from': ['D:\\Code\\CEM_Test\\src\\labcem\\kernels\\acoustic_kernel\\knowledge\\cards\\multi_ATH_-_Advanced-Transition_Horns_ATH_-_Segmentizing_a_horn_Ath-AP1_waveguide_card_001.json',
                    'D:\\Code\\CEM_Test\\src\\labcem\\kernels\\acoustic_kernel\\knowledge\\cards\\waveguide_design_waveguide_card_001.json'],
 'created_at': '2026-05-10T15:52:43.768568Z'}

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
