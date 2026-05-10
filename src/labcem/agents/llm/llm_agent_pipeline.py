from __future__ import annotations

from pathlib import Path
from typing import Dict

from .llm_client import LLMClient
from .llm_codegen_agent import LLMCodegenAgent
from .llm_config import LLMConfig
from .llm_knowledge_agent import LLMKnowledgeAgent
from .llm_review_agent import LLMReviewAgent
from .llm_schema_agent import LLMSchemaAgent


class LLMAgentPipeline:
    def __init__(self, kernels_root: Path):
        self.kernels_root = kernels_root
        self.config = LLMConfig.from_env(project_root=Path(__file__).resolve().parents[4])
        self.client = LLMClient(self.config)
        self.knowledge_agent = LLMKnowledgeAgent(kernels_root, self.client)
        self.schema_agent = LLMSchemaAgent(kernels_root, self.client)
        self.codegen_agent = LLMCodegenAgent(kernels_root, self.client)
        self.review_agent = LLMReviewAgent(kernels_root, self.client)

    def status(self) -> dict:
        return self.config.status_dict()

    def _disabled(self) -> Dict:
        return {
            "ok": False,
            "message": "LLM is not enabled. Set LABCEM_LLM_ENABLED=true and provide LABCEM_LLM_API_KEY.",
            "outputs": [],
            "warnings": [],
            "errors": [],
        }

    def llm_extract_knowledge(self, kernel_id: str, source_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return self._disabled()
        src_dir = self.kernels_root / kernel_id / "knowledge" / "sources"
        source_json_path = None
        for ext in [".clean_text.json", ".repo_summary.json"]:
            p = src_dir / f"{source_id}{ext}"
            if p.exists():
                source_json_path = p
                break
        if source_json_path is None:
            return {"ok": False, "message": f"source_id not found: {source_id}", "outputs": [], "warnings": [], "errors": []}
        return self.knowledge_agent.run(kernel_id, component_type, source_json_path)

    def llm_generate_schema(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return self._disabled()
        return self.schema_agent.run(kernel_id, component_type)

    def llm_propose_code(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return self._disabled()
        return self.codegen_agent.run(kernel_id, component_type)

    def llm_review(self, kernel_id: str, component_type: str) -> Dict:
        if not self.client.is_available():
            return self._disabled()
        return self.review_agent.run(kernel_id, component_type)
