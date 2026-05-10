import json
from pathlib import Path

from .geometry import GeometryObject


def export_geometry(geometry: GeometryObject, out_path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"kind": geometry.kind, "params": geometry.params}, indent=2), encoding="utf-8")
    return out
