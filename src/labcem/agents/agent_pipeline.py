from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .component_codegen_agent import ComponentCodegenAgent
from .document_importer import DocumentImporter
from .github_importer import GitHubImporter
from .kernel_review_agent import KernelReviewAgent
from .knowledge_extractor import KnowledgeExtractor
from .llm.llm_agent_pipeline import LLMAgentPipeline
from .schema_generator import SchemaGenerator


class DomainAgentPipeline:
    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"
        self.doc = DocumentImporter(self.kernels_root)
        self.repo = GitHubImporter(self.kernels_root)
        self.extractor = KnowledgeExtractor(self.kernels_root)
        self.schema_gen = SchemaGenerator(self.kernels_root)
        self.codegen = ComponentCodegenAgent(self.kernels_root)
        self.reviewer = KernelReviewAgent(self.kernels_root)
        self.llm = LLMAgentPipeline(self.kernels_root)

    def import_documents(self, kernel_id: str, paths: List[str]) -> Dict:
        try:
            res = self.doc.import_sources(kernel_id, paths)
            return {"ok": res.get("ok", False), "message": res.get("message", ""), "outputs": [res.get("output")], "source_id": res.get("source_id"), "errors": res.get("errors", [])}
        except Exception as exc:
            return {"ok": False, "message": f"import_documents failed: {exc}", "outputs": []}

    def import_github_repo(self, kernel_id: str, repo_path: str) -> Dict:
        try:
            res = self.repo.import_repo(kernel_id, repo_path)
            return {"ok": res.get("ok", False), "message": res.get("message", ""), "outputs": [res.get("output")], "source_id": res.get("source_id"), "errors": res.get("errors", [])}
        except Exception as exc:
            return {"ok": False, "message": f"import_github_repo failed: {exc}", "outputs": []}

    def llm_status(self) -> Dict:
        st = self.llm.status()
        return {"ok": True, **st}

    def _effective_mode(self, mode: str) -> str:
        m = (mode or "hybrid").lower()
        if m not in {"rules", "llm", "hybrid"}:
            m = "hybrid"
        if m in {"llm", "hybrid"} and not self.llm.client.is_available():
            return "rules" if m == "hybrid" else "llm"
        return m

    def extract_knowledge(self, kernel_id: str, source_id: str, component_type: str, mode: str = "hybrid") -> Dict:
        m = self._effective_mode(mode)
        if m == "rules":
            try:
                return self.extractor.extract(kernel_id, source_id, component_type)
            except Exception as exc:
                return {"ok": False, "message": f"extract_knowledge failed: {exc}", "outputs": []}
        if m == "llm":
            return self.llm.llm_extract_knowledge(kernel_id, source_id, component_type)
        # hybrid
        out = []
        warns = []
        rr = self.extract_knowledge(kernel_id, source_id, component_type, mode="rules")
        out.extend(rr.get("outputs", []))
        lr = self.llm.llm_extract_knowledge(kernel_id, source_id, component_type)
        out.extend(lr.get("outputs", []))
        warns.extend(lr.get("warnings", []))
        if not lr.get("ok"):
            warns.append("LLM unavailable in hybrid; kept rules outputs.")
        return {"ok": rr.get("ok", False), "message": "Hybrid extraction completed", "outputs": out, "warnings": warns, "errors": []}

    def generate_schema(self, kernel_id: str, component_type: str, mode: str = "hybrid") -> Dict:
        m = self._effective_mode(mode)
        if m == "rules":
            try:
                return self.schema_gen.generate(kernel_id, component_type)
            except Exception as exc:
                return {"ok": False, "message": f"generate_schema failed: {exc}", "outputs": []}
        if m == "llm":
            return self.llm.llm_generate_schema(kernel_id, component_type)
        rr = self.generate_schema(kernel_id, component_type, mode="rules")
        lr = self.llm.llm_generate_schema(kernel_id, component_type)
        return {
            "ok": rr.get("ok", False),
            "message": "Hybrid schema generation completed",
            "outputs": rr.get("outputs", []) + lr.get("outputs", []),
            "warnings": ([] if lr.get("ok") else ["LLM unavailable in hybrid; kept rules schema outputs."]) + lr.get("warnings", []),
            "errors": [],
        }

    def propose_code(self, kernel_id: str, component_type: str, mode: str = "hybrid") -> Dict:
        m = self._effective_mode(mode)
        if m == "rules":
            try:
                return self.codegen.propose(kernel_id, component_type)
            except Exception as exc:
                return {"ok": False, "message": f"propose_code failed: {exc}", "outputs": []}
        if m == "llm":
            return self.llm.llm_propose_code(kernel_id, component_type)
        rr = self.propose_code(kernel_id, component_type, mode="rules")
        lr = self.llm.llm_propose_code(kernel_id, component_type)
        return {
            "ok": rr.get("ok", False),
            "message": "Hybrid propose-code completed",
            "outputs": rr.get("outputs", []) + lr.get("outputs", []),
            "warnings": ([] if lr.get("ok") else ["LLM unavailable in hybrid; kept rules proposed code outputs."]) + lr.get("warnings", []),
            "errors": [],
        }

    def review_proposal(self, kernel_id: str, component_type: str, mode: str = "hybrid") -> Dict:
        m = self._effective_mode(mode)
        if m == "rules":
            try:
                return self.reviewer.review(kernel_id, component_type)
            except Exception as exc:
                return {"ok": False, "message": f"review_proposal failed: {exc}", "outputs": []}
        if m == "llm":
            # LLM review does not replace static review; run static first.
            sr = self.review_proposal(kernel_id, component_type, mode="rules")
            lr = self.llm.llm_review(kernel_id, component_type)
            return {
                "ok": sr.get("ok", False) and lr.get("ok", False),
                "message": "LLM review completed with static review",
                "outputs": sr.get("outputs", []) + lr.get("outputs", []),
                "warnings": lr.get("warnings", []),
                "errors": lr.get("errors", []),
            }
        sr = self.review_proposal(kernel_id, component_type, mode="rules")
        lr = self.llm.llm_review(kernel_id, component_type)
        warns = [] if lr.get("ok") else ["LLM unavailable in hybrid; static review kept."]
        return {
            "ok": sr.get("ok", False),
            "message": "Hybrid review completed",
            "outputs": sr.get("outputs", []) + lr.get("outputs", []),
            "warnings": warns + lr.get("warnings", []),
            "errors": lr.get("errors", []),
        }

    def detect_source_id(self, kernel_id: str, preferred: str | None = None) -> str | None:
        if preferred:
            return preferred
        src_dir = self.kernels_root / kernel_id / "knowledge" / "sources"
        if not src_dir.exists():
            return None
        files = sorted(src_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return None
        try:
            payload = json.loads(files[0].read_text(encoding="utf-8"))
            return payload.get("source_id")
        except Exception:
            return files[0].stem.split(".")[0]
