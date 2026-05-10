from __future__ import annotations

import math


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def expansion_profile(t: float, family: str = "tritonia", power: float = 1.35) -> float:
    t = _clamp01(t)
    power = max(0.05, float(power))
    fam = str(family or "tritonia").lower()

    if fam == "linear":
        p = t
    elif fam in {"osse", "os-se", "os_se", "oblate_spheroid", "oblate-spheroid"}:
        p = math.sin(t * math.pi * 0.5) ** power
    elif fam in {"tritonia_m", "tritonia-m", "tritonia m"}:
        tri = 0.5 - 0.5 * math.cos(math.pi * (t ** power))
        p = 0.65 * tri + 0.35 * t
    else:  # default tritonia
        p = 0.5 - 0.5 * math.cos(math.pi * (t ** power))

    return _clamp01(p)
