from labcem.l1.sdf_operations import intersect, offset, shell, smooth_union, subtract, union
from labcem.l1.sdf_primitives import (
    box_sdf,
    cylinder_sdf,
    hex_bolt_sdf,
    section_sdf_2d,
    sphere_sdf,
    torus_sdf,
    waveguide_profile,
)


def _as_float(value, default):
    return float(default if value is None else value)


def _waveguide_spec(params):
    throat = _as_float(params.get("throat_radius", 12.7), 12.7)
    mouth = _as_float(params.get("mouth_radius", 60.0), 60.0)
    mouth_w = _as_float(params.get("mouth_width", mouth * 2.0), mouth * 2.0)
    mouth_h = _as_float(params.get("mouth_height", mouth * 2.0), mouth * 2.0)
    spec = {
        "throat_radius": throat,
        "mouth_rx": mouth_w * 0.5,
        "mouth_ry": mouth_h * 0.5,
        "mouth_shape": str(params.get("mouth_shape", "ellipse")).lower(),
        "profile_type": str(params.get("waveguide_type", "oblate_spheroid")),
        "blend": _as_float(params.get("curve_blend", 0.35), 0.35),
        "depth": _as_float(params.get("depth", 35.0), 35.0),
        "wall_thickness": _as_float(params.get("wall_thickness", 3.0), 3.0),
        "roundover_radius": _as_float(params.get("roundover_radius", 8.0), 8.0),
        "throat_angle": _as_float(params.get("throat_angle", 10.0), 10.0),
        "term_s_base": _as_float(params.get("term_s_base", 0.7), 0.7),
        "term_s_cos2": _as_float(params.get("term_s_cos2", 0.2), 0.2),
        "term_n": _as_float(params.get("term_n", 3.7), 3.7),
        "term_q": _as_float(params.get("term_q", 0.992), 0.992),
        "morph_rate": _as_float(params.get("morph_rate", 3.0), 3.0),
        "morph_corner_radius": _as_float(params.get("morph_corner_radius", 18.0), 18.0),
        "mouth_flange_size": _as_float(params.get("mouth_flange_size", 10.0), 10.0),
        "throat_flange_size": _as_float(params.get("throat_flange_size", 6.0), 6.0),
        "front_only": bool(params.get("front_only", True)),
        "rib_style": str(params.get("reinforcement_style", "radial_ribs")).lower(),
        "rib_count": int(_as_float(params.get("reinforcement_count", 6), 6)),
        "rib_thickness": _as_float(params.get("reinforcement_thickness", 2.5), 2.5),
        "rib_height": _as_float(params.get("reinforcement_height", 8.0), 8.0),
        "rib_r0": _as_float(params.get("reinforcement_start_radius", max(throat * 0.75, 10.0)), max(throat * 0.75, 10.0)),
        "rib_r1": _as_float(params.get("reinforcement_end_radius", max(mouth_w * 0.35, throat + 10.0)), max(mouth_w * 0.35, throat + 10.0)),
        "baffle_width": _as_float(params.get("baffle_width", max(mouth_w + 24.0, 150.0)), max(mouth_w + 24.0, 150.0)),
        "baffle_height": _as_float(params.get("baffle_height", max(mouth_h + 24.0, 120.0)), max(mouth_h + 24.0, 120.0)),
        "baffle_thickness": _as_float(params.get("baffle_thickness", 5.0), 5.0),
    }
    return spec


def sdf_waveguide_acoustic_path(x, y, z, spec):
    depth = spec["depth"]
    if z < 0.0 or z > depth:
        return max(-z, z - depth)
    t = z / max(depth, 1e-6)
    rx, ry = waveguide_profile(t, spec)
    sq = 2.0 + 8.0 * (t ** 1.1) if spec["mouth_shape"] == "rect" else 2.0
    return section_sdf_2d(x, y, rx, ry, mouth_shape=spec["mouth_shape"], roundover=spec["roundover_radius"], squareness=sq)


def sdf_waveguide_outer_shell(x, y, z, spec):
    depth = spec["depth"]
    wall_t = spec["wall_thickness"]
    if z < 0.0 or z > depth:
        return max(-z, z - depth)
    t = z / max(depth, 1e-6)
    rx, ry = waveguide_profile(t, spec)
    orx = rx + wall_t
    ory = ry + wall_t
    sq = 2.0 + 8.0 * (t ** 1.1) if spec["mouth_shape"] == "rect" else 2.0
    outer = section_sdf_2d(x, y, orx, ory, mouth_shape=spec["mouth_shape"], roundover=spec["roundover_radius"], squareness=sq)
    inner = section_sdf_2d(x, y, rx, ry, mouth_shape=spec["mouth_shape"], roundover=spec["roundover_radius"], squareness=sq)
    # thin shell: inside outer AND outside inner
    return max(outer, -inner)


def sdf_mouth_flange(x, y, z, spec):
    fz = spec["depth"] + 0.5 * spec["wall_thickness"]
    ft = max(spec["wall_thickness"] * 1.3, 2.0)
    zloc = z - fz
    frame = box_sdf(x, y, zloc, spec["baffle_width"], spec["baffle_height"], ft)
    rx, ry = waveguide_profile(1.0, spec)
    cut = section_sdf_2d(x, y, rx + 0.35 * spec["wall_thickness"], ry + 0.35 * spec["wall_thickness"], mouth_shape=spec["mouth_shape"], roundover=spec["roundover_radius"], squareness=10.0)
    return max(frame, -cut)


def sdf_throat_mount(x, y, z, spec):
    mt = max(spec["wall_thickness"] * 1.6, 2.0)
    zloc = z + mt * 0.35
    base = cylinder_sdf(x, y, zloc, spec["throat_radius"] + spec["throat_flange_size"] + spec["wall_thickness"], mt)
    hole = cylinder_sdf(x, y, zloc, max(spec["throat_radius"], 1.0), mt * 1.4)
    return max(base, -hole)


def sdf_radial_ribs(x, y, z, spec):
    if spec["rib_style"] != "radial_ribs" or spec["rib_count"] <= 0:
        return 1e9
    import math

    d = 1e9
    rib_z = spec["depth"] * 0.35
    mid_r = 0.5 * (spec["rib_r0"] + spec["rib_r1"])
    rib_len = max(spec["rib_r1"] - spec["rib_r0"], 1.0)
    for i in range(max(spec["rib_count"], 1)):
        a = 2.0 * math.pi * i / max(spec["rib_count"], 1)
        ca = math.cos(a)
        sa = math.sin(a)
        xr = ca * x + sa * y
        yr = -sa * x + ca * y
        rib = box_sdf(xr - mid_r, yr, z - rib_z, rib_len, spec["rib_thickness"], spec["rib_height"])
        d = min(d, rib)
    return d


def _waveguide_solid_sdf(params):
    spec = _waveguide_spec(params)

    def _shell(x, y, z):
        return sdf_waveguide_outer_shell(x, y, z, spec)

    def _path(x, y, z):
        return sdf_waveguide_acoustic_path(x, y, z, spec)

    def _flange(x, y, z):
        return sdf_mouth_flange(x, y, z, spec)

    def _mount(x, y, z):
        return sdf_throat_mount(x, y, z, spec)

    def _ribs(x, y, z):
        return sdf_radial_ribs(x, y, z, spec)

    # Base open-front shell + flange + throat mount + ribs
    solid = lambda x, y, z: min(min(_shell(x, y, z), _flange(x, y, z)), min(_mount(x, y, z), _ribs(x, y, z)))
    # keep acoustic path fully clear through whole part
    final = lambda x, y, z: max(solid(x, y, z), -_path(x, y, z))
    span = max(spec["baffle_width"], spec["baffle_height"], spec["depth"] + spec["wall_thickness"] * 4.0) * 1.35
    return final, span


def validate_waveguide_topology(mesh_or_voxel, spec):
    vals = getattr(mesh_or_voxel, "values", None)
    if vals is None:
        return {}
    n = vals.shape[0]
    c = n // 2
    throat_open = bool(vals[c, c, 1] > 0.0)
    mouth_open = bool(vals[c, c, n - 2] > 0.0)
    mid_clear = bool(vals[c, c, n // 2] > 0.0)
    wall_t = float(spec.get("wall_thickness", 0.0))
    min_wall = float(spec.get("min_wall_thickness", 0.0) or 0.0)
    ribs_generated = bool(str(spec.get("reinforcement_style", "radial_ribs")).lower() == "radial_ribs" and int(spec.get("reinforcement_count", 0) or 0) > 0)
    return {
        "throat_open": throat_open,
        "mouth_open": mouth_open,
        "acoustic_path_clear": mid_clear,
        "front_only": bool(spec.get("front_only", True)),
        "closed_port": not (throat_open and mouth_open and mid_clear),
        "radial_ribs_generated": ribs_generated,
        "wall_thickness_ok": wall_t >= max(min_wall, 0.1),
    }


def build_sdf_from_params(params):
    shape = params.get("shape", "cylinder")
    if shape == "torus":
        major = _as_float(params.get("major_radius", 24.0), 24.0)
        minor = _as_float(params.get("minor_radius", 7.0), 7.0)
        span = (major + minor) * 2.6
        return lambda x, y, z: torus_sdf(x, y, z, major, minor), span
    if shape == "sphere":
        radius = _as_float(params.get("radius", 10.0), 10.0)
        return lambda x, y, z: sphere_sdf(x, y, z, radius), radius * 2.8
    if shape == "hex_bolt":
        sr = _as_float(params.get("shaft_radius", 2.0), 2.0)
        sl = _as_float(params.get("shaft_length", 26.0), 26.0)
        hr = _as_float(params.get("head_radius", 4.0), 4.0)
        hh = _as_float(params.get("head_height", 3.0), 3.0)
        span = max(hr * 3.0, (sl + hh) * 1.8)
        return lambda x, y, z: hex_bolt_sdf(x, y, z, sr, sl, hr, hh), span
    if shape in ("waveguide", "horn"):
        return _waveguide_solid_sdf(params)

    radius = _as_float(params.get("radius", 10.0), 10.0)
    height = _as_float(params.get("height", 40.0), 40.0)
    span = max(radius * 2.6, height * 1.4)
    return lambda x, y, z: cylinder_sdf(x, y, z, radius, height), span


def apply_sdf_operations(base_sdf, operations):
    sdf_fn = base_sdf
    op_log = []
    for op in operations:
        name = str(op.op).lower()
        cfg = op.params
        if name == "offset":
            delta = _as_float(cfg.get("delta", 0.0), 0.0)
            prev = sdf_fn
            sdf_fn = lambda x, y, z, p=prev, d=delta: offset(p(x, y, z), d)
            op_log.append(f"offset({delta})")
        elif name == "shell":
            t = _as_float(cfg.get("thickness", 1.0), 1.0)
            prev = sdf_fn
            sdf_fn = lambda x, y, z, p=prev, th=t: shell(p(x, y, z), th)
            op_log.append(f"shell({t})")
        elif name in ("union", "subtract", "intersect", "smooth_union"):
            prim = str(cfg.get("primitive", "sphere"))
            ox = _as_float(cfg.get("x", 0.0), 0.0)
            oy = _as_float(cfg.get("y", 0.0), 0.0)
            oz = _as_float(cfg.get("z", 0.0), 0.0)
            if prim == "box":
                sx = _as_float(cfg.get("sx", 8.0), 8.0)
                sy = _as_float(cfg.get("sy", 8.0), 8.0)
                sz = _as_float(cfg.get("sz", 8.0), 8.0)
                other = lambda x, y, z, a=sx, b=sy, c=sz, px=ox, py=oy, pz=oz: box_sdf(x - px, y - py, z - pz, a, b, c)
            else:
                rr = _as_float(cfg.get("radius", 4.0), 4.0)
                other = lambda x, y, z, r=rr, px=ox, py=oy, pz=oz: sphere_sdf(x - px, y - py, z - pz, r)
            prev = sdf_fn
            if name == "union":
                sdf_fn = lambda x, y, z, p=prev, q=other: union(p(x, y, z), q(x, y, z))
            elif name == "subtract":
                sdf_fn = lambda x, y, z, p=prev, q=other: subtract(p(x, y, z), q(x, y, z))
            elif name == "intersect":
                sdf_fn = lambda x, y, z, p=prev, q=other: intersect(p(x, y, z), q(x, y, z))
            else:
                kk = _as_float(cfg.get("k", 1.0), 1.0)
                sdf_fn = lambda x, y, z, p=prev, q=other, k=kk: smooth_union(p(x, y, z), q(x, y, z), k)
            op_log.append(name)
    return sdf_fn, op_log
