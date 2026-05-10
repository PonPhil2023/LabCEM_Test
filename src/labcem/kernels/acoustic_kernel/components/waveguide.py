from __future__ import annotations

from typing import Any, Dict

from labcem.core.plugin.component_builder import ComponentBuilder


class WaveguideBuilder(ComponentBuilder):
    component_type = "waveguide"
    display_name = "Waveguide"
    domain = "acoustic"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": [
                "throat_diameter",
                "mouth_width",
                "mouth_height",
                "depth",
                "directivity_h",
                "directivity_v",
                "wall_thickness",
                "flange_thickness",
                "resolution",
            ],
        }

    def solve_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(spec)
        out.setdefault("component_type", "waveguide")
        out.setdefault("family", "tritonia")
        out.setdefault("profile_family", out.get("family", "tritonia"))
        out.setdefault("throat_diameter", 50.0)
        out.setdefault("mouth_width", 200.0)
        out.setdefault("mouth_height", 140.0)
        out.setdefault("depth", 95.0)
        out.setdefault("directivity_h", 90.0)
        out.setdefault("directivity_v", 60.0)
        out.setdefault("coverage_h", out.get("directivity_h"))
        out.setdefault("coverage_v", out.get("directivity_v"))
        out.setdefault("segments", 96)
        out.setdefault("angular_segments", 144)
        out.setdefault("wall_thickness", 3.0)
        out.setdefault("flange_thickness", 4.0)
        out.setdefault("flange_margin", 12.0)
        out.setdefault("roundover_radius", 8.0)
        out.setdefault("throat_roundover", 3.0)
        out.setdefault("throat_adapter_depth", 8.0)
        out.setdefault("profile_power", 1.35)
        out.setdefault("morph_rate", 1.0)
        out.setdefault("resolution", 36)
        return out

    def build(self, spec: Dict[str, Any], backend: Any):
        model = backend.build_waveguide_sdf(spec)
        if isinstance(model, dict) and isinstance(model.get("validation"), dict):
            spec["__waveguide_validation__"] = model["validation"]
        return model

    def validate(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        errs = []
        if float(spec["mouth_width"]) <= float(spec["throat_diameter"]):
            errs.append("mouth_width must be larger than throat_diameter")
        if float(spec["mouth_height"]) <= float(spec["throat_diameter"]):
            errs.append("mouth_height must be larger than throat_diameter")
        if float(spec["depth"]) <= 0:
            errs.append("depth must be > 0")
        return {"ok": len(errs) == 0, "errors": errs}

    def metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "display_name": self.display_name,
            "domain": self.domain,
            "design_params": {k: spec.get(k) for k in [
                "family", "profile_family", "throat_diameter", "mouth_width", "mouth_height", "depth", "directivity_h", "directivity_v", "coverage_h", "coverage_v",
                "segments", "angular_segments", "wall_thickness", "flange_thickness", "flange_margin", "roundover_radius", "throat_roundover", "throat_adapter_depth",
                "profile_power", "morph_rate", "resolution"
            ]},
        }
