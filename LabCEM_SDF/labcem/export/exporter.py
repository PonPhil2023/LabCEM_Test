from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ..core.spec import AcousticShape


@dataclass
class ExportManager:
    def export_stl(self, shape: AcousticShape, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        shape.mesh.export(out)
        return out

    def export_3mf(self, shape: AcousticShape, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        shape.mesh.export(out)
        return out

    def export_vdb(self, shape: AcousticShape, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("VDB export placeholder for Stage-3 OpenVDB backend.", encoding="utf-8")
        return out

    def export_report_json(self, report: Dict, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


_exporter = ExportManager()


def export_stl(shape: AcousticShape, path: str):
    return _exporter.export_stl(shape, path)
