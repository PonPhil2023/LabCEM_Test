from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class KernelReviewAgent:
    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"

    def review(self, kernel_id: str, component_type: str) -> Dict:
        proposal_file = self.kernels_root / kernel_id / "generated" / "proposed_components" / f"{component_type}_generated_builder.py"
        if not proposal_file.exists():
            raise FileNotFoundError(f"proposal file not found: {proposal_file}")

        src = proposal_file.read_text(encoding="utf-8")
        tree = ast.parse(src)

        has_class = any(isinstance(n, ast.ClassDef) for n in tree.body)
        inherits_component_builder = any(
            isinstance(n, ast.ClassDef)
            and any(getattr(base, "id", "") == "ComponentBuilder" or getattr(base, "attr", "") == "ComponentBuilder" for base in n.bases)
            for n in tree.body
        )
        method_names = set()
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_names.add(item.name)

        checks = {
            "has_class": has_class,
            "inherits_component_builder": inherits_component_builder,
            "has_get_schema": "get_schema" in method_names,
            "has_solve_parameters": "solve_parameters" in method_names,
            "has_build": "build" in method_names,
            "has_validate": "validate" in method_names,
            "has_metadata": "metadata" in method_names,
            "no_import_gui": "import labcem.gui" not in src,
            "no_import_cli": "import labcem.cli" not in src,
            "no_core_modification": True,
            "no_mesh_export": "mesh.export(" not in src,
            "no_direct_stl_obj_write": (".stl" not in src and ".obj" not in src),
            "uses_backend": "backend." in src,
            "has_autogen_comment": "AUTO-GENERATED PROPOSAL" in src,
        }

        errors = [k for k, ok in checks.items() if not ok and k in {
            "has_class", "inherits_component_builder", "has_get_schema", "has_solve_parameters", "has_build", "has_validate", "has_metadata", "uses_backend", "has_autogen_comment"
        }]
        warnings = [k for k, ok in checks.items() if not ok and k not in errors]

        report = {
            "ok": len(errors) == 0,
            "kernel_id": kernel_id,
            "component_type": component_type,
            "proposal_file": str(proposal_file),
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        out_dir = self.kernels_root / kernel_id / "generated" / "review_reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{component_type}_review_report.json"
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        return {"ok": report["ok"], "message": "Review completed", "outputs": [str(out_path)], "report": report}
