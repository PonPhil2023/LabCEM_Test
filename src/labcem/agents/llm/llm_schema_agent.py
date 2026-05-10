from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .llm_client import LLMClient
from .prompt_templates import SCHEMA_GENERATION_SYSTEM_PROMPT, SCHEMA_GENERATION_USER_TEMPLATE
from .response_schemas import COMPONENT_SCHEMA_SCHEMA


class LLMSchemaAgent:
    def __init__(self, kernels_root: Path, llm_client: LLMClient):
        self.kernels_root = kernels_root
        self.client = llm_client

    def run(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return {"ok": False, "message": "LLM unavailable", "outputs": [], "warnings": [], "errors": []}

        kdir = self.kernels_root / kernel_id / "knowledge"
        cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kdir / "cards").glob("*.json"))]
        formulas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kdir / "formulas").glob("*.json"))]
        rules = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((kdir / "rules").glob("*.json"))]

        user_prompt = SCHEMA_GENERATION_USER_TEMPLATE.format(
            kernel_id=kernel_id,
            component_type=component_type,
            knowledge_cards=json.dumps(cards[:30], ensure_ascii=False),
            formula_cards=json.dumps(formulas[:30], ensure_ascii=False),
            rules=json.dumps(rules[:30], ensure_ascii=False),
        )
        res = self.client.complete_json(SCHEMA_GENERATION_SYSTEM_PROMPT, user_prompt, COMPONENT_SCHEMA_SCHEMA)
        if not res.get("ok"):
            return {"ok": False, "message": "LLM schema generation failed", "outputs": [], "warnings": [], "errors": [res.get("message", "unknown")]}

        out = self.kernels_root / kernel_id / "schemas" / f"{component_type}_schema.llm.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "message": "LLM schema generated", "outputs": [str(out)], "warnings": res.get("warnings", []), "errors": []}
