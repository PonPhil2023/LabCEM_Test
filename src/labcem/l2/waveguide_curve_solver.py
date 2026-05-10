from dataclasses import asdict, dataclass


@dataclass
class WaveguideProfile:
    profile_type: str
    points: list


def _curve_s(tt, ptype):
    if ptype == "conical":
        return tt
    if ptype == "exponential":
        return (2.5 ** tt - 1.0) / 1.5
    if ptype == "bezier":
        u = 1.0 - tt
        return (u ** 3) * 0.0 + 3 * (u ** 2) * tt * 0.12 + 3 * u * (tt ** 2) * 0.72 + (tt ** 3)
    if ptype == "os_like":
        return 1.0 - (max(0.0, 1.0 - tt * tt) ** 0.5)
    if ptype == "superellipse_loft":
        return (3.0 * tt * tt - 2.0 * tt * tt * tt) ** 0.95
    return 3.0 * tt * tt - 2.0 * tt * tt * tt


def solve_waveguide_curve(requirement, target, profile_type=None, section_count=56, wall_thickness=None):
    ptype = profile_type or target.profile_hint or "os_like"
    throat_r = float(requirement.throat_diameter_mm) * 0.5
    mouth_rx = float(target.mouth_width_mm) * 0.5
    mouth_ry = float(target.mouth_height_mm) * 0.5
    depth = float(target.depth_estimate_mm)
    wall = float(wall_thickness if wall_thickness is not None else requirement.min_wall_thickness_mm)

    rows = []
    n = max(16, int(section_count))
    prev_area = None
    for i in range(n):
        t = i / float(n - 1)
        s = max(0.0, min(1.0, _curve_s(t, ptype)))
        rx = throat_r + (mouth_rx - throat_r) * s
        ry = throat_r + (mouth_ry - throat_r) * s
        z = depth * t
        area = 3.1415926535 * rx * ry
        exp_rate = 0.0 if prev_area is None else (area - prev_area) / max(prev_area, 1e-6)
        prev_area = area
        rows.append(
            {
                "z": z,
                "t": t,
                "rx": rx,
                "ry": ry,
                "area": area,
                "local_expansion_rate": exp_rate,
                "inner_contour": {"rx": rx, "ry": ry},
                "outer_contour": {"rx": rx + wall, "ry": ry + wall},
                "mouth_interp_factor": s,
            }
        )
    return WaveguideProfile(profile_type=ptype, points=rows)


def profile_to_dict(profile):
    return asdict(profile)

