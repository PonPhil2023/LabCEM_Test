from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from .llm_client import LLMClient
from .prompt_templates import REVIEW_SYSTEM_PROMPT, REVIEW_USER_TEMPLATE
from .response_schemas import REVIEW_SCHEMA


class LLMReviewAgent:
    def __init__(self, kernels_root: Path, llm_client: LLMClient):
        self.kernels_root = kernels_root
        self.client = llm_client

    def run(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return {"ok": False, "message": "LLM unavailable", "outputs": [], "warnings": [], "errors": []}

        proposal_file = self.kernels_root / kernel_id / "generated" / "proposed_components" / f"{component_type}_llm_builder.py"
        if not proposal_file.exists():
            proposal_file = self.kernels_root / kernel_id / "generated" / "proposed_components" / f"{component_type}_generated_builder.py"
        if not proposal_file.exists():
            return {"ok": False, "message": "No proposal file found for LLM review", "outputs": [], "warnings": [], "errors": []}

        code_text = proposal_file.read_text(encoding="utf-8")
        user_prompt = REVIEW_USER_TEMPLATE.format(kernel_id=kernel_id, component_type=component_type, code_text=code_text[:50000])
        res = self.client.complete_json(REVIEW_SYSTEM_PROMPT, user_prompt, REVIEW_SCHEMA)
        if not res.get("ok"):
            return {"ok": False, "message": "LLM review failed", "outputs": [], "warnings": [], "errors": [res.get("message", "unknown")]}

        report = {"ok": True, "llm_review": res, "static_review_required": True, "created_at": datetime.utcnow().isoformat() + "Z"}
        out = self.kernels_root / kernel_id / "generated" / "review_reports" / f"{component_type}_llm_review_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "message": "LLM review completed", "outputs": [str(out)], "warnings": [], "errors": []}
