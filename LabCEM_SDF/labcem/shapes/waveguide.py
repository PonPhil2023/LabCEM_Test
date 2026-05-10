from __future__ import annotations

from typing import Dict, Union

from ..core.backends import SDFBackend, backend_factory
from ..core.spec import AcousticShape, DesignSpec
from .builders import WaveguideBuilder


def create_waveguide(spec: Union[DesignSpec, Dict], backend: Union[str, SDFBackend] = "python_sdf") -> AcousticShape:
    design = spec if isinstance(spec, DesignSpec) else DesignSpec.from_dict(spec)
    be = backend_factory(backend) if isinstance(backend, str) else backend
    return WaveguideBuilder(be).build(design)
