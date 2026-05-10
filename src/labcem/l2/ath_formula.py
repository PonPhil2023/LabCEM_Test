import math


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _parse_band(band):
    if not band:
        return 2000.0, 10000.0
    s = str(band).lower().replace("hz", "").strip()
    if "-" in s:
        a, b = s.split("-", 1)
        try:
            return float(a), float(b)
        except Exception:
            return 2000.0, 10000.0
    return 2000.0, 10000.0


def ath_trial_from_params(params):
    throat_d = float(params.get("throat_diameter", {}).get("value", 25.4) or 25.4)
    mouth_w = float(params.get("mouth_width", {}).get("value", 120.0) or 120.0)
    mouth_h = float(params.get("mouth_height", {}).get("value", 90.0) or 90.0)
    depth = float(params.get("depth", {}).get("value", 35.0) or 35.0)
    band = params.get("frequency_band", {}).get("value", "2000-10000")

    f1, f2 = _parse_band(band)
    center = math.sqrt(max(f1, 1.0) * max(f2, 1.0))
    aspect = max(mouth_w / max(mouth_h, 1e-6), 1.0)

    # ATH/OS-SE/R-OSSE style heuristics:
    # a  : nominal coverage half-angle
    # a0 : throat opening half-angle
    # k  : throat expansion factor
    # q  : throat shape factor
    # m  : superellipse blend/termination weight
    # b  : rollback-like control
    L = depth
    r0 = throat_d * 0.5
    a0 = _clamp(3.0 + 12.0 * (r0 / max(L, 1e-6)), 3.0, 18.0)
    flare = _clamp(32.0 + 22.0 * (1000.0 / max(center, 500.0)), 26.0, 70.0)
    ripple = _clamp(4.0 + 4.0 * (aspect - 1.0), 3.0, 10.0)
    expo_weight = _clamp((3500.0 - center) / 3000.0, 0.15, 0.75)
    cov_half = _clamp(0.5 * (90.0 if aspect <= 1.4 else 80.0), 30.0, 55.0)

    k = _clamp(1.0 + 0.9 * (r0 / max(L, 1e-6)), 0.9, 1.8)
    q = _clamp(2.8 + 1.6 * (aspect - 1.0), 2.2, 4.8)
    m = _clamp(0.55 + 0.25 * (aspect - 1.0), 0.45, 0.9)
    b = _clamp(0.10 + 0.35 * expo_weight, 0.05, 0.45)

    if center < 1800:
        profile = "exponential"
        mode = "Tritonia"
    elif aspect > 1.5:
        profile = "tractrix"
        mode = "Tritonia-M"
    else:
        profile = "oblate_spheroid"
        mode = "OS-SE"

    geometry_family = "R-OSSE" if profile in ("oblate_spheroid", "tractrix") else "ATH"
    a_expr = "{0:.2f} - {1:.2f}*cos(2.0*p)^5".format(flare, ripple)

    return {
        "mode": mode,
        "geometry_family": geometry_family,
        "profile": profile,
        "curve_blend": round(float(expo_weight), 3),
        "ath_params": {
            "L": round(L, 3),
            "r0": round(r0, 3),
            "a": round(cov_half, 3),
            "a0": round(a0, 3),
            "k": round(k, 4),
            "q": round(q, 4),
            "m": round(m, 4),
            "b": round(b, 4),
            "a_expr": a_expr,
            "center_hz": round(center, 2),
        },
    }
