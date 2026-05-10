from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OperationNode:
    op: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationGraph:
    intent: str
    backend: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    operations: List[OperationNode] = field(default_factory=list)

    @classmethod
    def from_instruction(cls, instruction: Dict[str, Any]) -> "OperationGraph":
        default_ops = [
            {"op": "create_baffle"},
            {"op": "create_acoustic_path"},
            {"op": "boolean_subtract"},
            {"op": "add_roundover"},
            {"op": "add_radial_ribs"},
            {"op": "add_screw_holes"},
            {"op": "validate_mesh"},
            {"op": "export_stl"},
        ]
        src_ops = instruction.get("operations", []) or default_ops
        ops = [OperationNode(op=item.get("op", ""), params={k: v for k, v in item.items() if k != "op"}) for item in src_ops]
        intent = instruction.get("intent") or f"create_{instruction.get('shape', 'geometry')}"
        backend = instruction.get("backend", "sdf")
        return cls(intent=intent, backend=backend, parameters=dict(instruction), operations=ops)

