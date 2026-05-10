from __future__ import annotations

from dataclasses import dataclass

from ..core.backends import SDFBackend
from ..core.spec import AcousticShape, DesignSpec


@dataclass
class WaveguideBuilder:
    backend: SDFBackend

    def build(self, spec: DesignSpec) -> AcousticShape:
        return self.backend.create_waveguide(spec)


@dataclass
class HornBuilder:
    backend: SDFBackend

    def build(self, spec: DesignSpec) -> AcousticShape:
        return self.backend.create_waveguide(spec)


@dataclass
class CavityBuilder:
    backend: SDFBackend

    def build(self, spec: DesignSpec) -> AcousticShape:
        return self.backend.create_waveguide(spec)


@dataclass
class PortBuilder:
    backend: SDFBackend

    def build(self, spec: DesignSpec) -> AcousticShape:
        return self.backend.create_waveguide(spec)
