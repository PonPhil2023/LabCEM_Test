import re
from dataclasses import asdict, dataclass


@dataclass
class WaveguideRequirement:
    throat_diameter_mm: float = 25.4
    throat_shape: str = "circle"
    f_low_hz: float = 2000.0
    f_high_hz: float = 10000.0
    horizontal_coverage_deg: float = 90.0
    vertical_coverage_deg: float = 60.0
    max_width_mm: float = 160.0
    max_height_mm: float = 110.0
    max_depth_mm: float = 75.0
    min_wall_thickness_mm: float = 3.0
    manufacturing_method: str = "FDM"
    preferred_profile_type: str = "os_like"


def _first_float(patterns, text):
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None


def _extract_band(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k)?\s*hz\s*(?:到|-|~|to)\s*(\d+(?:\.\d+)?)\s*(k)?\s*hz", text, flags=re.IGNORECASE)
    if not m:
        return None, None
    f1 = float(m.group(1)) * (1000.0 if m.group(2) else 1.0)
    f2 = float(m.group(3)) * (1000.0 if m.group(4) else 1.0)
    return min(f1, f2), max(f1, f2)


def parse_waveguide_requirement(text, overrides=None):
    src = text or ""
    req = WaveguideRequirement()
    low, high = _extract_band(src)
    if low:
        req.f_low_hz = low
        req.f_high_hz = high

    td = _first_float(
        [
            r"throat[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
            r"入口[^0-9]{0,20}(?:直徑)?[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm",
            r"喉口[^0-9]{0,20}(?:直徑)?[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm",
        ],
        src,
    )
    if td:
        req.throat_diameter_mm = td

    hw = _first_float([r"horizontal[^0-9]{0,20}(\d+(?:\.\d+)?)", r"水平[^0-9]{0,20}(\d+(?:\.\d+)?)"], src)
    vw = _first_float([r"vertical[^0-9]{0,20}(\d+(?:\.\d+)?)", r"垂直[^0-9]{0,20}(\d+(?:\.\d+)?)"], src)
    if hw:
        req.horizontal_coverage_deg = hw
    if vw:
        req.vertical_coverage_deg = vw

    mw = _first_float([r"(?:max|maxim(?:um)?)\s*(?:width|w)[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm", r"最大寬度[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm"], src)
    mh = _first_float([r"(?:max|maxim(?:um)?)\s*(?:height|h)[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm", r"最大高度[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm"], src)
    md = _first_float([r"(?:max|maxim(?:um)?)\s*depth[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm", r"深度不超過[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm"], src)
    if mw:
        req.max_width_mm = mw
    if mh:
        req.max_height_mm = mh
    if md:
        req.max_depth_mm = md

    # mouth dimensions fallback: "180x120mm"
    mwh = re.search(r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm", src)
    if mwh:
        req.max_width_mm = float(mwh.group(1))
        req.max_height_mm = float(mwh.group(2))

    wt = _first_float([r"wall[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm", r"壁厚[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm"], src)
    if wt:
        req.min_wall_thickness_mm = wt

    if "sla" in src.lower():
        req.manufacturing_method = "SLA"
    if "fdm" in src.lower() or "3d 列印" in src.lower():
        req.manufacturing_method = "FDM"

    profile_alias = {
        "tritonia": "tritonia_m",
        "r-osse": "r_osse",
        "rosse": "r_osse",
        "os-se": "os_se",
        "osse": "os_se",
        "ath": "ath",
        "conical": "conical",
        "exponential": "exponential",
        "bezier": "bezier",
        "os_like": "os_like",
        "superellipse_loft": "superellipse_loft",
    }
    for key, val in profile_alias.items():
        if key in src.lower():
            req.preferred_profile_type = val
            break

    if overrides:
        for k, v in overrides.items():
            if hasattr(req, k) and v is not None:
                setattr(req, k, v)
    return req


def requirement_to_dict(req):
    return asdict(req)


def is_target_waveguide_prompt(text):
    t = (text or "").lower()
    has_band = ("hz" in t) or ("khz" in t) or ("頻寬" in (text or ""))
    has_cov = ("horizontal" in t) or ("vertical" in t) or ("水平" in (text or "")) or ("垂直" in (text or ""))
    has_size = ("最大寬度" in (text or "")) or ("最大高度" in (text or "")) or ("max width" in t) or ("max height" in t) or bool(re.search(r"\d+\s*[xX×]\s*\d+\s*mm", text or ""))
    has_wave_word = ("waveguide" in t) or ("波導" in (text or "")) or ("號角" in (text or "")) or ("throat" in t) or ("喉口" in (text or "")) or ("入口" in (text or ""))
    # CEM target-driven trigger: either explicit waveguide word, or enough target cues.
    return bool(has_wave_word or (has_band and has_cov and has_size))
