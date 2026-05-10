from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from .ath_like_profiles import expansion_profile


def _safe_pow_signed(v: np.ndarray, e: float) -> np.ndarray:
    return np.sign(v) * (np.abs(v) ** e)


def superellipse_points(width: float, height: float, exponent: float, z: float, angular_segments: int) -> np.ndarray:
    a = max(1e-6, float(width) * 0.5)
    b = max(1e-6, float(height) * 0.5)
    n = max(2.0, float(exponent))
    m = max(8, int(angular_segments))

    theta = np.linspace(0.0, 2.0 * math.pi, num=m, endpoint=False, dtype=np.float64)
    c = np.cos(theta)
    s = np.sin(theta)
    x = a * _safe_pow_signed(c, 2.0 / n)
    y = b * _safe_pow_signed(s, 2.0 / n)
    z_arr = np.full_like(x, float(z))
    return np.column_stack((x, y, z_arr))


def ring_params_at_t(
    t: float,
    family: str,
    throat_diameter: float,
    mouth_width: float,
    mouth_height: float,
    profile_power: float,
    morph_rate: float,
) -> Tuple[float, float, float, float]:
    p = expansion_profile(t, family=family, power=profile_power)
    p_m = max(0.0, min(1.0, p ** max(0.2, morph_rate)))

    width_t = throat_diameter + p * (mouth_width - throat_diameter)
    height_t = throat_diameter + p * (mouth_height - throat_diameter)
    exponent_t = 2.0 + p_m * 6.0
    return width_t, height_t, exponent_t, p
