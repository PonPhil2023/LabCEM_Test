from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class ExportManager:
    def export_mesh(self, mesh: Any, path: str):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(p)
        return p

    def export_json(self, data: Dict, path: str):
        import json

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p
