from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .formula_extractor import FormulaExtractor


class KnowledgeExtractor:
    COMPONENT_KEYWORDS = [
        "waveguide", "horn", "diffuser", "cavity", "port", "baffle", "波導", "號角", "擴散板", "腔體", "導管",
    ]
    WAVEGUIDE_PARAM_KEYWORDS = [
        "throat", "mouth", "depth", "width", "height", "coverage", "directivity", "flare", "profile", "superellipse",
        "tractrix", "exponential", "conical", "wall thickness", "flange", "喉口", "入口", "出口", "深度", "寬度", "高度",
        "指向性", "擴張率", "曲線", "壁厚", "法蘭",
    ]

    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"
        self.formula_extractor = FormulaExtractor()

    def extract(self, kernel_id: str, source_id: str, component_type: str) -> Dict:
        source_payload, source_path = self._load_source(kernel_id, source_id)
        text = source_payload.get("combined_text", "")
        low = text.lower()

        knowledge_dir = self.kernels_root / kernel_id / "knowledge"
        cards_dir = knowledge_dir / "cards"
        formulas_dir = knowledge_dir / "formulas"
        rules_dir = knowledge_dir / "rules"
        for d in [cards_dir, formulas_dir, rules_dir]:
            d.mkdir(parents=True, exist_ok=True)

        card = self._build_card(kernel_id, component_type, source_id, text, low)
        card_path = cards_dir / f"{source_id}_{component_type}_card_001.json"
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

        formulas = self.formula_extractor.extract(text)
        formula_payload = {
            "id": f"{kernel_id}_{component_type}_formula_001",
            "kernel_id": kernel_id,
            "component_type": component_type,
            "source_id": source_id,
            "formulas": formulas,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        formula_path = formulas_dir / f"{source_id}_{component_type}_formulas_001.json"
        formula_path.write_text(json.dumps(formula_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        rule = self._build_rule(kernel_id, component_type, source_id, low)
        rule_path = rules_dir / f"{source_id}_{component_type}_rule_001.json"
        rule_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "ok": True,
            "message": "Knowledge extracted",
            "outputs": [str(card_path), str(formula_path), str(rule_path)],
            "source_file": str(source_path),
        }

    def _load_source(self, kernel_id: str, source_id: str):
        src_dir = self.kernels_root / kernel_id / "knowledge" / "sources"
        for suffix in [".clean_text.json", ".repo_summary.json"]:
            p = src_dir / f"{source_id}{suffix}"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8")), p
        raise FileNotFoundError(f"source_id not found: {source_id}")

    def _build_card(self, kernel_id: str, component_type: str, source_id: str, text: str, low: str) -> Dict:
        params = {}
        for kw in self.WAVEGUIDE_PARAM_KEYWORDS:
            if kw.lower() in low:
                params[kw] = True
        detected_components: List[str] = [kw for kw in self.COMPONENT_KEYWORDS if kw.lower() in low]
        summary = f"Detected {len(detected_components)} component keywords and {len(params)} waveguide parameter keywords."

        hints = []
        if "wall thickness" in low or "壁厚" in low:
            hints.append("Enforce minimum wall thickness for manufacturability.")
        if "directivity" in low or "指向性" in low:
            hints.append("Keep directivity targets in solve_parameters().")

        return {
            "id": "acoustic_waveguide_card_001",
            "kernel_id": kernel_id,
            "domain": "acoustic" if "acoustic" in kernel_id else "general",
            "component_type": component_type,
            "knowledge_type": "geometry_rule",
            "title": "Detected waveguide design knowledge",
            "summary": summary,
            "parameters": params,
            "formulas": self.formula_extractor.extract(text),
            "implementation_hints": hints,
            "source_id": source_id,
            "confidence": 0.5,
            "review_status": "pending",
        }

    def _build_rule(self, kernel_id: str, component_type: str, source_id: str, low: str) -> Dict:
        description = "Detected general geometry/manufacturing rule candidates."
        if "fdm" in low or "print" in low or "列印" in low:
            description = "FDM/printing constraints detected; ensure adequate wall thickness and flange support."
        return {
            "id": "acoustic_waveguide_rule_001",
            "kernel_id": kernel_id,
            "component_type": component_type,
            "rule_type": "manufacturing_or_geometry",
            "description": description,
            "severity": "info",
            "source_id": source_id,
        }
