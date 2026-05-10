from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .llm_client import LLMClient
from .prompt_templates import CODEGEN_SYSTEM_PROMPT, CODEGEN_USER_TEMPLATE
from .response_schemas import CODEGEN_SCHEMA


class LLMCodegenAgent:
    def __init__(self, kernels_root: Path, llm_client: LLMClient):
        self.kernels_root = kernels_root
        self.client = llm_client

    def run(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return {"ok": False, "message": "LLM unavailable", "outputs": [], "warnings": [], "errors": []}

        kernel_dir = self.kernels_root / kernel_id
        schema_path = kernel_dir / "schemas" / f"{component_type}_schema.llm.json"
        if not schema_path.exists():
            schema_path = kernel_dir / "schemas" / f"{component_type}_schema.json"
        if not schema_path.exists():
            return {"ok": False, "message": "No schema found for codegen", "outputs": [], "warnings": [], "errors": []}

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kernel_dir / "knowledge" / "cards").glob("*.json"))]
        formulas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kernel_dir / "knowledge" / "formulas").glob("*.json"))]
        rules = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kernel_dir / "knowledge" / "rules").glob("*.json"))]
        codegen_rules_path = Path(__file__).resolve().parents[4] / "docs" / "CODEGEN_RULES.md"
        codegen_rules = codegen_rules_path.read_text(encoding="utf-8") if codegen_rules_path.exists() else ""

        user_prompt = CODEGEN_USER_TEMPLATE.format(
            kernel_id=kernel_id,
            component_type=component_type,
            schema_json=json.dumps(schema, ensure_ascii=False),
            knowledge_cards=json.dumps(cards[:20], ensure_ascii=False),
            formula_cards=json.dumps(formulas[:20], ensure_ascii=False),
            rules=json.dumps(rules[:20], ensure_ascii=False),
            codegen_rules=codegen_rules[:12000],
        )
        res = self.client.complete_json(CODEGEN_SYSTEM_PROMPT, user_prompt, CODEGEN_SCHEMA)
        if not res.get("ok"):
            return {"ok": False, "message": "LLM codegen failed", "outputs": [], "warnings": [], "errors": [res.get("message", "unknown")]}

        comp_dir = kernel_dir / "generated" / "proposed_components"
        solver_dir = kernel_dir / "generated" / "proposed_solvers"
        test_dir = kernel_dir / "generated" / "proposed_tests"
        for d in [comp_dir, solver_dir, test_dir]:
            d.mkdir(parents=True, exist_ok=True)

        comp_name = f"{component_type}_llm_builder.py"
        solver_name = f"{component_type}_llm_solver.py"
        test_name = f"test_{component_type}_llm_builder.py"

        comp_content = (res.get("component_file", {}) or {}).get("content", "")
        solver_content = (res.get("solver_file", {}) or {}).get("content", "")
        test_content = (res.get("test_file", {}) or {}).get("content", "")

        if "AUTO-GENERATED PROPOSAL" not in comp_content:
            comp_content = "# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY\n" + comp_content
        if "AUTO-GENERATED PROPOSAL" not in solver_content:
            solver_content = "# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY\n" + solver_content
        if "AUTO-GENERATED PROPOSAL" not in test_content:
            test_content = "# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY\n" + test_content

        cp = comp_dir / comp_name
        sp = solver_dir / solver_name
        tp = test_dir / test_name
        cp.write_text(comp_content, encoding="utf-8")
        sp.write_text(solver_content, encoding="utf-8")
        tp.write_text(test_content, encoding="utf-8")

        warnings = list(res.get("warnings", []))
        banned_tokens = ["mesh.export(", ".stl", ".obj", "import labcem.gui", "import labcem.cli"]
        if any(tok in comp_content for tok in banned_tokens):
            warnings.append("Potential policy violation found in generated component code; static review required.")

        return {"ok": True, "message": "LLM proposed code generated", "outputs": [str(cp), str(sp), str(tp)], "warnings": warnings, "errors": []}
