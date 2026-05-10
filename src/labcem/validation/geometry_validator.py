from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class GeometryValidator:
    def __init__(self) -> None:
        self.issues: List[str] = []

    def validate_required_fields(self, spec: Dict[str, Any]) -> bool:
        required = ["type", "throat_diameter", "mouth_width", "mouth_height", "depth", "wall_thickness"]
        ok = True
        for key in required:
            if key not in spec:
                self.issues.append("missing_required_field:{0}".format(key))
                ok = False
        return ok

    def validate_dimension_range(self, spec: Dict[str, Any]) -> bool:
        checks = [
            ("throat_diameter", 1.0, 200.0),
            ("mouth_width", 5.0, 2000.0),
            ("mouth_height", 5.0, 2000.0),
            ("depth", 5.0, 2000.0),
            ("wall_thickness", 0.5, 100.0),
        ]
        ok = True
        for name, lo, hi in checks:
            v = float(spec.get(name, 0.0) or 0.0)
            if not (lo <= v <= hi):
                self.issues.append("dimension_out_of_range:{0}={1}".format(name, v))
                ok = False
        return ok

    def validate_wall_thickness(self, spec: Dict[str, Any]) -> bool:
        wall = float(spec.get("wall_thickness", 0.0) or 0.0)
        throat = float(spec.get("throat_diameter", 0.0) or 0.0)
        ok = wall > 0.0 and wall < throat * 0.45
        if not ok:
            self.issues.append("invalid_wall_thickness")
        return ok

    def validate_mesh_exists(self, mesh: Any) -> bool:
        ok = mesh is not None and hasattr(mesh, "vertices") and len(mesh.vertices) > 0 and len(mesh.faces) > 0
        if not ok:
            self.issues.append("mesh_not_generated")
        return ok

    def validate_export_success(self, export_path: Path) -> bool:
        p = Path(export_path)
        ok = p.exists() and p.stat().st_size > 128
        if not ok:
            self.issues.append("export_failed")
        return ok

    def export_validation_report(self, report: Dict[str, Any], path: Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return p
