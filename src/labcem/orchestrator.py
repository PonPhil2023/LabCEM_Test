from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from labcem.core.pipeline.build_pipeline import BuildPipeline
from labcem.core.plugin.backend_registry import BackendRegistry
from labcem.core.plugin.kernel_manager import KernelManager


class LabCEMOrchestrator:
    """Facade shared by GUI and CLI."""

    def __init__(self, knowledge_root="knowledge/domains", model_path=None):
        self.knowledge_root = Path(knowledge_root)
        self.model_path = model_path
        self.kernel_manager = KernelManager()
        self.backend_registry = BackendRegistry()
        self.pipeline = BuildPipeline(self.kernel_manager, self.backend_registry)

    def run_from_prompt(
        self,
        prompt: str,
        domain: str = "acoustic",
        kernel: str = "acoustic_kernel",
        backend: str = "python_sdf",
        component_type: str = "waveguide",
        output: Optional[str] = None,
        voxel_resolution: int = 36,
    ) -> Dict[str, Any]:
        spec = self._parse_prompt_to_spec(prompt, default_component=component_type)
        spec.setdefault("domain", domain)
        spec.setdefault("component_type", component_type)
        spec["resolution"] = int(voxel_resolution)
        return self.run_from_spec(spec=spec, kernel=kernel, backend=backend, output=output)

    def run_from_spec(
        self,
        spec: Dict[str, Any],
        output: Optional[str] = None,
        kernel: str = "acoustic_kernel",
        backend: str = "python_sdf",
    ) -> Dict[str, Any]:
        return self.pipeline.run(spec=spec, kernel_id=kernel, backend_id=backend, output=output)

    # Backward compatible entry for existing GUI/CLI calls.
    def run(self, spec, domain, output_path, voxel_resolution=24, use_lattice=False, attachment_path=""):
        mapped_domain = "acoustic" if (domain or "general").lower() == "general" else domain
        return self.run_from_prompt(
            prompt=spec,
            domain=mapped_domain,
            kernel="acoustic_kernel",
            backend="python_sdf",
            output=output_path,
            component_type="waveguide",
            voxel_resolution=int(voxel_resolution),
        )

    def _parse_prompt_to_spec(self, prompt: str, default_component: str = "waveguide") -> Dict[str, Any]:
        text = prompt or ""
        s = text.lower()
        component = default_component or "waveguide"
        for c in ["waveguide", "horn", "diffuser", "cavity", "port"]:
            if re.search(rf"\b{c}\b", s):
                component = c
                break
        if any(k in text for k in ["波導", "号角", "號角", "导波"]):
            component = "waveguide"

        family = "tritonia"
        if re.search(r"\blinear\b", s):
            family = "linear"
        elif re.search(r"\bos[\s\-_]*se\b", s) or "oblate" in s or "os-se" in s or "osse" in s:
            family = "osse"
        elif "tritonia-m" in s or "tritonia_m" in s or "tritonia m" in s:
            family = "tritonia_m"
        elif "tritonia" in s:
            family = "tritonia"

        spec: Dict[str, Any] = {
            "component_type": component,
            "family": family,
            "profile_family": family,
            "throat_diameter": 50.0,
            "mouth_width": 200.0,
            "mouth_height": 140.0,
            "depth": 95.0,
            "directivity_h": 90.0,
            "directivity_v": 60.0,
            "wall_thickness": 3.0,
            "flange_thickness": 4.0,
            "segments": 96,
            "angular_segments": 144,
            "flange_margin": 12.0,
            "roundover_radius": 8.0,
            "throat_roundover": 3.0,
            "throat_adapter_depth": 8.0,
            "profile_power": 1.35,
            "morph_rate": 1.0,
            "resolution": 36,
        }

        throat = re.search(r"(?:throat(?:\s*diameter)?|喉口(?:為圓形)?(?:直徑)?|入口(?:直徑)?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*mm?", s)
        if not throat:
            throat = re.search(r"直徑\s*([0-9]+(?:\.[0-9]+)?)\s*mm?", s)
        if throat:
            spec["throat_diameter"] = float(throat.group(1))

        mouth = re.search(r"(?:mouth|出口)\s*([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)", s)
        if not mouth:
            mouth = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)\s*mm?", s)
        if mouth:
            spec["mouth_width"] = float(mouth.group(1))
            spec["mouth_height"] = float(mouth.group(2))

        depth = re.search(r"(?:depth|深度)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", s)
        if depth:
            spec["depth"] = float(depth.group(1))

        dir_h = re.search(r"(?:directivity_h|horizontal(?:\s*directivity)?|水平(?:指向性|覆蓋角)?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", s)
        if dir_h:
            spec["directivity_h"] = float(dir_h.group(1))
            spec["coverage_h"] = float(dir_h.group(1))

        dir_v = re.search(r"(?:directivity_v|vertical(?:\s*directivity)?|垂直(?:指向性|覆蓋角)?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", s)
        if dir_v:
            spec["directivity_v"] = float(dir_v.group(1))
            spec["coverage_v"] = float(dir_v.group(1))

        wall = re.search(r"wall(?:_thickness)?\s*([0-9]+(?:\.[0-9]+)?)", s)
        if wall:
            spec["wall_thickness"] = float(wall.group(1))

        flange = re.search(r"flange(?:_thickness)?\s*([0-9]+(?:\.[0-9]+)?)", s)
        if flange:
            spec["flange_thickness"] = float(flange.group(1))

        return spec
