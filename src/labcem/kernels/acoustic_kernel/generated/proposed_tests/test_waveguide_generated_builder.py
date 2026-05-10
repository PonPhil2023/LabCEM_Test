# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY
from __future__ import annotations

from labcem.kernels.acoustic_kernel.generated.proposed_components.waveguide_generated_builder import WaveguideGeneratedBuilder


def test_generated_builder_contract():
    b = WaveguideGeneratedBuilder()
    spec = b.solve_parameters({"component_type": "waveguide"})
    assert b.get_schema()
    assert spec["component_type"] == "waveguide"
