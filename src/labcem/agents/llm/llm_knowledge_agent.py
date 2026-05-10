from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from .llm_client import LLMClient
from .prompt_templates import KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT, KNOWLEDGE_EXTRACTION_USER_TEMPLATE
from .response_schemas import KNOWLEDGE_EXTRACTION_SCHEMA


class LLMKnowledgeAgent:
    def __init__(self, kernels_root: Path, llm_client: LLMClient):
        self.kernels_root = kernels_root
        self.client = llm_client

    def run(self, kernel_id: str, component_type: str, source_json_path: Path) -> Dict:
        if not self.client.is_available():
            return {"ok": False, "message": "LLM unavailable", "outputs": [], "warnings": [], "errors": []}

        payload = json.loads(source_json_path.read_text(encoding="utf-8"))
        source_id = payload.get("source_id", source_json_path.stem)
        source_text = payload.get("combined_text", "")
        user_prompt = KNOWLEDGE_EXTRACTION_USER_TEMPLATE.format(
            kernel_id=kernel_id, component_type=component_type, source_id=source_id, source_text=source_text[:50000]
        )
        res = self.client.complete_json(KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT, user_prompt, KNOWLEDGE_EXTRACTION_SCHEMA)
        if not res.get("ok"):
            return {"ok": False, "message": "LLM extraction failed", "outputs": [], "warnings": [], "errors": [res.get("message", "unknown")]}

        knowledge_dir = self.kernels_root / kernel_id / "knowledge"
        cards_dir = knowledge_dir / "cards"
        formulas_dir = knowledge_dir / "formulas"
        rules_dir = knowledge_dir / "rules"
        for d in [cards_dir, formulas_dir, rules_dir]:
            d.mkdir(parents=True, exist_ok=True)

        outs = []
        now = datetime.utcnow().isoformat() + "Z"
        for i, c in enumerate(res.get("knowledge_cards", []) or []):
            c["source_id"] = source_id
            c["kernel_id"] = kernel_id
            c["component_type"] = component_type
            c["created_by"] = "llm"
            c["created_at"] = now
            c["review_status"] = "pending"
            p = cards_dir / f"{source_id}_{component_type}_llm_card_{i+1:03d}.json"
            p.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
            outs.append(str(p))

        formulas_payload = {
            "source_id": source_id,
            "kernel_id": kernel_id,
            "component_type": component_type,
            "created_by": "llm",
            "created_at": now,
            "formula_cards": res.get("formula_cards", []),
        }
        fp = formulas_dir / f"{source_id}_{component_type}_llm_formulas.json"
        fp.write_text(json.dumps(formulas_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        outs.append(str(fp))

        rules_payload = {
            "source_id": source_id,
            "kernel_id": kernel_id,
            "component_type": component_type,
            "created_by": "llm",
            "created_at": now,
            "rules": res.get("rules", []),
        }
        rp = rules_dir / f"{source_id}_{component_type}_llm_rules.json"
        rp.write_text(json.dumps(rules_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        outs.append(str(rp))

        warnings = res.get("warnings", [])
        if not res.get("knowledge_cards") and not res.get("formula_cards") and not res.get("rules"):
            warnings.append("LLM returned empty extraction")
        return {"ok": True, "message": "LLM knowledge extraction completed", "outputs": outs, "warnings": warnings, "errors": []}
