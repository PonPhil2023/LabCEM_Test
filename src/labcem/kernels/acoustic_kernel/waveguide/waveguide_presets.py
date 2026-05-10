from __future__ import annotations

from .waveguide_schema import WaveguideSpec


def get_waveguide_preset(name: str = "tritonia") -> WaveguideSpec:
    key = str(name or "tritonia").lower()
    if key in {"osse", "os-se", "os_se"}:
        return WaveguideSpec(family="osse", profile_power=1.25, throat_diameter=50.0, mouth_width=200.0, mouth_height=140.0, depth=95.0)
    if key in {"tritonia_m", "tritonia-m"}:
        return WaveguideSpec(family="tritonia_m", profile_power=1.4, throat_diameter=50.0, mouth_width=200.0, mouth_height=140.0, depth=95.0)
    if key == "linear":
        return WaveguideSpec(family="linear", profile_power=1.0, throat_diameter=50.0, mouth_width=200.0, mouth_height=140.0, depth=95.0)
    return WaveguideSpec(family="tritonia", profile_power=1.35, throat_diameter=50.0, mouth_width=200.0, mouth_height=140.0, depth=95.0)
