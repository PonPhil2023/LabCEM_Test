from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class SchemaGenerator:
    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"

    def generate(self, kernel_id: str, component_type: str) -> Dict:
        schemas_dir = self.kernels_root / kernel_id / "schemas"
        cards_dir = self.kernels_root / kernel_id / "knowledge" / "cards"
        schemas_dir.mkdir(parents=True, exist_ok=True)

        generated_from: List[str] = [str(p) for p in sorted(cards_dir.glob(f"*_{component_type}_card_*.json"))]

        if kernel_id == "acoustic_kernel" and component_type == "waveguide":
            schema = self._waveguide_schema(generated_from)
        else:
            schema = {
                "kernel_id": kernel_id,
                "domain": kernel_id.replace("_kernel", ""),
                "component_type": component_type,
                "display_name": component_type.title(),
                "aliases": [component_type],
                "parameters": {},
                "generated_from": generated_from,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

        out_path = schemas_dir / f"{component_type}_schema.json"
        out_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "message": "Schema generated", "outputs": [str(out_path)]}

    def _waveguide_schema(self, generated_from: List[str]) -> Dict:
        return {
            "kernel_id": "acoustic_kernel",
            "domain": "acoustic",
            "component_type": "waveguide",
            "display_name": "Waveguide",
            "aliases": ["waveguide", "波導", "號角導波器"],
            "parameters": {
                "throat_diameter": {"type": "float", "unit": "mm", "required": True, "default": 25.0, "aliases": ["throat", "throat diameter", "喉口", "入口", "入口直徑"]},
                "mouth_width": {"type": "float", "unit": "mm", "required": True, "default": 180.0, "aliases": ["mouth width", "出口寬度", "出口寬", "mouth_w"]},
                "mouth_height": {"type": "float", "unit": "mm", "required": True, "default": 120.0, "aliases": ["mouth height", "出口高度", "出口高", "mouth_h"]},
                "depth": {"type": "float", "unit": "mm", "required": True, "default": 90.0, "aliases": ["depth", "length", "深度", "波導深度"]},
                "directivity_h": {"type": "float", "unit": "deg", "required": False, "default": 90.0, "aliases": ["horizontal directivity", "水平指向性", "水平覆蓋角"]},
                "directivity_v": {"type": "float", "unit": "deg", "required": False, "default": 60.0, "aliases": ["vertical directivity", "垂直指向性", "垂直覆蓋角"]},
                "wall_thickness": {"type": "float", "unit": "mm", "required": False, "default": 3.0, "aliases": ["wall thickness", "壁厚"]},
                "flange_thickness": {"type": "float", "unit": "mm", "required": False, "default": 8.0, "aliases": ["flange", "flange thickness", "法蘭", "法蘭厚度"]},
                "flare_profile": {"type": "enum", "unit": "-", "required": False, "default": "superellipse", "choices": ["linear", "superellipse", "exponential", "tractrix", "conical"], "aliases": ["flare", "profile", "curve", "曲線", "擴張曲線"]},
                "resolution": {"type": "float", "unit": "mm", "required": False, "default": 1.0, "aliases": ["resolution", "解析度"]},
            },
            "generated_from": generated_from,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
