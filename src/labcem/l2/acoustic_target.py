from dataclasses import asdict, dataclass


@dataclass
class WaveguideAcousticTarget:
    mode: str = "rule_based_estimate"
    mouth_width_mm: float = 160.0
    mouth_height_mm: float = 110.0
    aspect_ratio: float = 1.45
    depth_estimate_mm: float = 55.0
    profile_hint: str = "os_like"
    target_band: tuple = (2000.0, 10000.0)
    target_coverage_deg: tuple = (90.0, 60.0)


def build_acoustic_target(requirement):
    low = max(200.0, float(requirement.f_low_hz))
    high = max(low + 10.0, float(requirement.f_high_hz))
    hcov = max(20.0, float(requirement.horizontal_coverage_deg))
    vcov = max(20.0, float(requirement.vertical_coverage_deg))

    # Heuristic estimates (not FEM/BEM).
    mouth_w = min(float(requirement.max_width_mm), max(90.0, 260000.0 / low * (90.0 / hcov)))
    mouth_h = min(float(requirement.max_height_mm), max(70.0, 210000.0 / low * (60.0 / vcov)))
    depth = min(float(requirement.max_depth_mm), max(28.0, 0.45 * (mouth_w - requirement.throat_diameter_mm)))
    ar = mouth_w / max(mouth_h, 1e-6)

    hint = requirement.preferred_profile_type or "os_like"
    if hint in ("r_osse", "os_se", "ath"):
        hint = "r_osse_like" if hint == "r_osse" else ("os_se_like" if hint == "os_se" else "ath_like")
    return WaveguideAcousticTarget(
        mouth_width_mm=mouth_w,
        mouth_height_mm=mouth_h,
        aspect_ratio=ar,
        depth_estimate_mm=depth,
        profile_hint=hint,
        target_band=(low, high),
        target_coverage_deg=(hcov, vcov),
    )


def acoustic_target_to_dict(t):
    return asdict(t)
