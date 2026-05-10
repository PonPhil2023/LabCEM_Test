import math


def check_waveguide_rules(params):
    warnings = []
    checks = {}

    throat = float(params.get("throat_diameter", {}).get("value", 0.0) or 0.0)
    mouth_w = float(params.get("mouth_width", {}).get("value", 0.0) or 0.0)
    mouth_h = float(params.get("mouth_height", {}).get("value", 0.0) or 0.0)
    depth = float(params.get("depth", {}).get("value", 0.0) or 0.0)
    band = str(params.get("frequency_band", {}).get("value", ""))

    try:
        a, b = band.split("-", 1)
        f1, f2 = float(a), float(b)
    except Exception:
        f1, f2 = 2000.0, 10000.0

    throat_area = math.pi * (throat * 0.5) ** 2
    mouth_area = max(mouth_w, 0.0) * max(mouth_h, 0.0)
    area_ratio = mouth_area / max(throat_area, 1e-6)
    checks["area_ratio"] = area_ratio

    if area_ratio < 2.5:
        warnings.append("Mouth/throat area ratio is low; directivity control may be weak.")
    if depth < throat * 0.45:
        warnings.append("Depth is shallow for the given throat size.")
    if mouth_w <= throat or mouth_h <= throat:
        warnings.append("Mouth size should exceed throat diameter.")
    if f1 < 800 and mouth_w < 220:
        warnings.append("Low crossover band may require larger mouth width.")

    checks["flare_smoothness_ok"] = depth > 0 and mouth_w > throat and mouth_h > throat
    checks["target_band"] = [f1, f2]
    return warnings, checks
