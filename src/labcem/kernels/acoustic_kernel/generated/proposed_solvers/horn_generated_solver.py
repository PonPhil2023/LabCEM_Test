# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from typing import Dict, Any


def solve_horn_parameters(spec: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(spec)
    out.setdefault("component_type", "horn")
    for name, cfg in schema.get("parameters", {}).items():
        if isinstance(cfg, dict) and "default" in cfg:
            out.setdefault(name, cfg.get("default"))
    return out
