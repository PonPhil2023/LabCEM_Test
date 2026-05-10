from __future__ import annotations

import json
import pprint
from pathlib import Path
from typing import Dict


class ComponentCodegenAgent:
    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"

    def propose(self, kernel_id: str, component_type: str) -> Dict:
        kernel_dir = self.kernels_root / kernel_id
        schema_path = kernel_dir / "schemas" / f"{component_type}_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"schema not found: {schema_path}")

        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        comp_dir = kernel_dir / "generated" / "proposed_components"
        solver_dir = kernel_dir / "generated" / "proposed_solvers"
        test_dir = kernel_dir / "generated" / "proposed_tests"
        for d in [comp_dir, solver_dir, test_dir]:
            d.mkdir(parents=True, exist_ok=True)

        builder_path = comp_dir / f"{component_type}_generated_builder.py"
        solver_path = solver_dir / f"{component_type}_generated_solver.py"
        test_path = test_dir / f"test_{component_type}_generated_builder.py"

        builder_path.write_text(self._builder_code(schema), encoding="utf-8")
        solver_path.write_text(self._solver_code(component_type), encoding="utf-8")
        test_path.write_text(self._test_code(kernel_id, component_type), encoding="utf-8")

        return {"ok": True, "message": "Proposed code generated", "outputs": [str(builder_path), str(solver_path), str(test_path)]}

    def _builder_code(self, schema: Dict) -> str:
        component_type = schema.get("component_type", "component")
        display_name = schema.get("display_name", component_type.title())
        domain = schema.get("domain", "general")
        class_name = f"{component_type.title().replace('_', '')}GeneratedBuilder"
        schema_literal = pprint.pformat(schema, width=100, sort_dicts=False)

        return f'''# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from typing import Any, Dict

from labcem.core.plugin.component_builder import ComponentBuilder


class {class_name}(ComponentBuilder):
    component_type = "{component_type}"
    display_name = "{display_name}"
    domain = "{domain}"

    def get_schema(self) -> Dict[str, Any]:
        return {schema_literal}

    def solve_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(spec)
        out.setdefault("component_type", self.component_type)
        for name, cfg in self.get_schema().get("parameters", {{}}).items():
            if isinstance(cfg, dict) and "default" in cfg:
                out.setdefault(name, cfg.get("default"))
        return out

    def build(self, spec: Dict[str, Any], backend: Any):
        return backend.build_waveguide_sdf(spec)

    def validate(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {{"ok": True, "errors": []}}

    def metadata(self, model: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {{
            "component_type": self.component_type,
            "display_name": self.display_name,
            "domain": self.domain,
            "generated": True,
        }}
'''

    def _solver_code(self, component_type: str) -> str:
        return f'''# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from typing import Dict, Any


def solve_{component_type}_parameters(spec: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(spec)
    out.setdefault("component_type", "{component_type}")
    for name, cfg in schema.get("parameters", {{}}).items():
        if isinstance(cfg, dict) and "default" in cfg:
            out.setdefault(name, cfg.get("default"))
    return out
'''

    def _test_code(self, kernel_id: str, component_type: str) -> str:
        class_name = f"{component_type.title().replace('_', '')}GeneratedBuilder"
        return f'''# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from labcem.kernels.{kernel_id}.generated.proposed_components.{component_type}_generated_builder import {class_name}


def test_generated_builder_contract():
    b = {class_name}()
    spec = b.solve_parameters({{"component_type": "{component_type}"}})
    assert b.get_schema()
    assert spec["component_type"] == "{component_type}"
'''
