from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_stl(mesh: Any, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(p)
    return p


def export_obj(mesh: Any, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(p)
    return p


def export_report_json(report: dict, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
