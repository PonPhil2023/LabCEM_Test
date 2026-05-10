import math


def sphere_sdf(x, y, z, radius):
    return math.sqrt(x * x + y * y + z * z) - radius


def cylinder_sdf(x, y, z, radius, height):
    radial = math.sqrt(x * x + y * y) - radius
    axial = abs(z) - (height / 2.0)
    return max(radial, axial)


def box_sdf(x, y, z, sx, sy, sz):
    dx = abs(x) - sx / 2.0
    dy = abs(y) - sy / 2.0
    dz = abs(z) - sz / 2.0
    outside = math.sqrt(max(dx, 0.0) ** 2 + max(dy, 0.0) ** 2 + max(dz, 0.0) ** 2)
    inside = min(max(dx, max(dy, dz)), 0.0)
    return outside + inside


def torus_sdf(x, y, z, major_radius, minor_radius):
    qx = math.sqrt(x * x + y * y) - major_radius
    return math.sqrt(qx * qx + z * z) - minor_radius


def hex_prism_sdf(x, y, z, radius, height):
    k = 0.8660254
    px = abs(x)
    py = abs(y)
    d1 = max(px * k + py * 0.5, py) - radius
    d2 = abs(z) - (height / 2.0)
    return max(d1, d2)


def hex_bolt_sdf(x, y, z, shaft_radius, shaft_length, head_radius, head_height):
    shaft_center_z = -head_height / 2.0 - shaft_length / 2.0
    shaft = cylinder_sdf(x, y, z - shaft_center_z, shaft_radius, shaft_length)
    head = hex_prism_sdf(x, y, z, head_radius, head_height)
    return min(shaft, head)


def _smoothstep(tt):
    return 3.0 * tt * tt - 2.0 * tt * tt * tt


def _bezier_cubic(tt, p0, p1, p2, p3):
    u = 1.0 - tt
    return (u ** 3) * p0 + 3.0 * (u ** 2) * tt * p1 + 3.0 * u * (tt ** 2) * p2 + (tt ** 3) * p3


def _clamp01(x):
    return min(max(x, 0.0), 1.0)


def _tritonia_progress(tt, params):
    # p in ATH scripts is typically normalized along the profile.
    p = _clamp01(tt) * (math.pi * 0.5)
    throat_angle = float(params.get("throat_angle", 10.0))
    term_s_base = float(params.get("term_s_base", 0.7))
    term_s_cos2 = float(params.get("term_s_cos2", 0.2))
    term_n = max(1.2, float(params.get("term_n", 3.7)))
    term_q = min(max(float(params.get("term_q", 0.992)), 0.5), 1.2)
    morph_rate = max(0.2, float(params.get("morph_rate", 3.0)))

    # Coverage.Angle = 48.5 - 7*cos(2*p)^5 - 16*sin(p)^12
    cov = 48.5 - 7.0 * (math.cos(2.0 * p) ** 5) - 16.0 * (math.sin(p) ** 12)
    cov_norm = min(max(cov / 48.5, 0.35), 1.25)

    # Term.s = 0.7 + 0.2*cos(p)^2, Term.n=3.7, Term.q=0.992
    term_s = term_s_base + term_s_cos2 * (math.cos(p) ** 2)
    zshape = tt ** (1.0 / term_q) if term_q > 0 else tt
    morph = 1.0 - math.exp(-morph_rate * tt)
    s = (_smoothstep(zshape) * cov_norm * term_s) ** (1.0 / term_n)

    # Throat angle softly biases early expansion.
    throat_bias = min(max(throat_angle / 45.0, 0.0), 0.5) * (tt ** 0.7)
    return _clamp01(0.82 * s + 0.18 * morph + 0.08 * throat_bias)


def waveguide_radius(t, throat_radius, mouth_radius, profile_type="oblate_spheroid", blend=0.35, extra_params=None):
    tt = _clamp01(t)
    p = (profile_type or "oblate_spheroid").lower()

    s_smooth = _smoothstep(tt)
    ratio = max(mouth_radius / max(throat_radius, 1e-6), 1e-6)
    s_exp = (ratio ** tt - 1.0) / max(ratio - 1.0, 1e-6)
    s_tractrix = 1.0 - math.sqrt(max(1.0 - tt, 0.0))

    s_poly = tt ** max(1.0, 1.6 + 2.4 * min(max(float(blend), 0.0), 1.0))
    s_oblate = 1.0 - math.sqrt(max(1.0 - (tt * tt), 0.0))
    s_bezier = _bezier_cubic(tt, 0.0, 0.12, 0.72, 1.0)
    s_compound = (0.45 * s_smooth) + (0.35 * s_exp) + (0.20 * s_tractrix)

    if p in ("tritonia_m", "tritonia", "ath_tritonia_m"):
        s = _tritonia_progress(tt, extra_params or {})
    elif p == "exponential":
        s = s_exp
    elif p == "tractrix":
        s = s_tractrix
    elif p in ("polynomial", "poly"):
        s = s_poly
    elif p in ("bezier", "bézier"):
        s = s_bezier
    elif p in ("oblate_spheroid", "os", "oblate"):
        s = s_oblate
    elif p in ("compound", "composite", "hybrid"):
        s = s_compound
    elif p in ("smoothstep", "smooth"):
        s = s_smooth
    else:
        b = min(max(float(blend), 0.0), 1.0)
        s = (1.0 - b) * s_smooth + b * s_exp

    # Enforce monotonic growth and avoid foldback in profile.
    s = min(max(s, 0.0), 1.0)
    return throat_radius + (mouth_radius - throat_radius) * s


def waveguide_profile(t, spec):
    """
    t: 0.0 ~ 1.0
    return rx, ry
    """
    tt = _clamp01(t)
    throat = float(spec.get("throat_radius", 12.7))
    mouth_rx = float(spec.get("mouth_rx", spec.get("mouth_width", 120.0) * 0.5))
    mouth_ry = float(spec.get("mouth_ry", spec.get("mouth_height", 90.0) * 0.5))
    ptype = str(spec.get("profile_type", "oblate_spheroid"))
    blend = float(spec.get("blend", 0.35))
    rx = waveguide_radius(tt, throat, mouth_rx, profile_type=ptype, blend=blend, extra_params=spec)
    ry = waveguide_radius(tt, throat, mouth_ry, profile_type=ptype, blend=blend, extra_params=spec)
    return max(rx, throat), max(ry, throat)


def section_sdf_2d(x, y, rx, ry, mouth_shape="ellipse", roundover=0.0, squareness=8.0):
    ms = (mouth_shape or "ellipse").lower()
    if ms in ("round", "circle"):
        r = max(min(rx, ry), 1e-6)
        return math.sqrt(x * x + y * y) - r
    if ms in ("rect", "rectangle"):
        n = max(2.0, float(squareness))
        ax = abs(x) / max(rx, 1e-6)
        ay = abs(y) / max(ry, 1e-6)
        d = (ax ** n + ay ** n) ** (1.0 / n) - 1.0
        return d * min(rx, ry) - max(roundover, 0.0) * 0.2
    nx = x / max(rx, 1e-6)
    ny = y / max(ry, 1e-6)
    return (math.sqrt(nx * nx + ny * ny) - 1.0) * min(rx, ry)


def waveguide_sdf(x, y, z, throat_radius, mouth_radius, depth, profile_type="oblate_spheroid", blend=0.35):
    t = (z + depth / 2.0) / max(depth, 1e-6)
    r = waveguide_radius(t, throat_radius, mouth_radius, profile_type=profile_type, blend=blend)
    radial = math.sqrt(x * x + y * y) - r
    axial = max(abs(z) - depth / 2.0, 0.0)
    return max(radial, axial)


def waveguide_elliptic_sdf(
    x,
    y,
    z,
    throat_radius,
    mouth_rx,
    mouth_ry,
    depth,
    profile_type="oblate_spheroid",
    blend=0.35,
):
    t = (z + depth / 2.0) / max(depth, 1e-6)
    rx = waveguide_radius(t, throat_radius, mouth_rx, profile_type=profile_type, blend=blend)
    ry = waveguide_radius(t, throat_radius, mouth_ry, profile_type=profile_type, blend=blend)
    nx = x / max(rx, 1e-6)
    ny = y / max(ry, 1e-6)
    radial = math.sqrt(nx * nx + ny * ny) - 1.0
    radial_mm = radial * min(rx, ry)
    axial = max(abs(z) - depth / 2.0, 0.0)
    return max(radial_mm, axial)


def waveguide_rect_morph_sdf(
    x,
    y,
    z,
    throat_radius,
    mouth_hw,
    mouth_hh,
    depth,
    profile_type="oblate_spheroid",
    blend=0.35,
):
    t = min(max((z + depth / 2.0) / max(depth, 1e-6), 0.0), 1.0)
    # Expand a bit earlier to avoid a long cylindrical section near throat.
    tz = t ** 0.88
    rx = waveguide_radius(tz, throat_radius, mouth_hw, profile_type=profile_type, blend=blend)
    ry = waveguide_radius(tz, throat_radius, mouth_hh, profile_type=profile_type, blend=blend)

    # Circle(throat) -> rounded-rect(mouth) via superellipse exponent.
    # n=2 is ellipse/circle, larger n trends to rectangle.
    n = 2.0 + 8.0 * (t ** 1.15)
    radial = section_sdf_2d(x, y, rx, ry, mouth_shape="rect", squareness=n)
    axial = max(abs(z) - depth / 2.0, 0.0)
    return max(radial, axial)


def sample_waveguide_profile(
    throat_radius,
    mouth_rx,
    mouth_ry,
    depth,
    profile_type="oblate_spheroid",
    blend=0.35,
    count=64,
):
    rows = []
    n = max(int(count), 4)
    for i in range(n):
        t = i / float(n - 1)
        z = -depth * 0.5 + depth * t
        rx = waveguide_radius(t, throat_radius, mouth_rx, profile_type=profile_type, blend=blend)
        ry = waveguide_radius(t, throat_radius, mouth_ry, profile_type=profile_type, blend=blend)
        rows.append({"z": round(z, 6), "rx": round(rx, 6), "ry": round(ry, 6)})
    return rows
