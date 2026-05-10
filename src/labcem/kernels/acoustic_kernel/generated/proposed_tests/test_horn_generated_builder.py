# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from labcem.kernels.acoustic_kernel.generated.proposed_components.horn_generated_builder import HornGeneratedBuilder


def test_generated_builder_contract():
    b = HornGeneratedBuilder()
    spec = b.solve_parameters({"component_type": "horn"})
    assert b.get_schema()
    assert spec["component_type"] == "horn"
