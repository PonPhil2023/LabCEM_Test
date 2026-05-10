from __future__ import annotations

from dataclasses import dataclass

from ..core.spec import DesignSpec


@dataclass
class DesignSolver:
    """Rule-based filler for missing acoustic parameters."""

    def solve(self, spec: DesignSpec) -> DesignSpec:
        if spec.wall_thickness <= 0:
            spec.wall_thickness = 3.0
        if spec.flange_thickness <= 0:
            spec.flange_thickness = 8.0
        return spec
