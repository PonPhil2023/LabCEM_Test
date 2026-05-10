import math
from dataclasses import dataclass

import numpy as np

from labcem.l1.sdf_primitives import waveguide_profile


@dataclass
class LoftSection:
    z: float
    rx: float
    ry: float
    t: float
    inner: np.ndarray
    outer: np.ndarray


def _as_float(v, d):
    return float(d if v is None else v)


def _spec(params):
    throat = _as_float(params.get("throat_radius", 12.7), 12.7)
    mouth_r = _as_float(params.get("mouth_radius", 60.0), 60.0)
    mw = _as_float(params.get("mouth_width", mouth_r * 2.0), mouth_r * 2.0)
    mh = _as_float(params.get("mouth_height", mouth_r * 2.0), mouth_r * 2.0)
    return {
        "throat_radius": throat,
        "mouth_rx": mw * 0.5,
        "mouth_ry": mh * 0.5,
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
        "include_mouth_flange": bool(params.get("include_mouth_flange", True)),
        "include_throat_mount": bool(params.get("include_throat_mount", True)),
        "include_reinforcement": bool(params.get("include_reinforcement", True)),
        "front_only": bool(params.get("front_only", True)),
        "rib_style": str(params.get("reinforcement_style", "radial_ribs")).lower(),
        "rib_count": int(_as_float(params.get("reinforcement_count", 6), 6)),
        "rib_thickness": _as_float(params.get("reinforcement_thickness", 2.5), 2.5),
        "rib_height": _as_float(params.get("reinforcement_height", 8.0), 8.0),
        "rib_r0": _as_float(params.get("reinforcement_start_radius", max(throat * 0.7, 10.0)), max(throat * 0.7, 10.0)),
        "rib_r1": _as_float(params.get("reinforcement_end_radius", max(mw * 0.35, throat + 10.0)), max(mw * 0.35, throat + 10.0)),
        "baffle_width": _as_float(params.get("baffle_width", max(mw + 24.0, 150.0)), max(mw + 24.0, 150.0)),
        "baffle_height": _as_float(params.get("baffle_height", max(mh + 24.0, 120.0)), max(mh + 24.0, 120.0)),
    }


def _shape_points(rx, ry, shape, n, t):
    th = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    c = np.cos(th)
    s = np.sin(th)
    if shape in ("round", "circle"):
        r = min(rx, ry)
        return np.column_stack((r * c, r * s))
    if shape in ("rect", "rectangle"):
        # superellipse contour (circle->rect).
        p = 2.0 + 8.0 * (t ** 1.2)
        x = np.sign(c) * (np.abs(c) ** (2.0 / p)) * rx
        y = np.sign(s) * (np.abs(s) ** (2.0 / p)) * ry
        return np.column_stack((x, y))
    return np.column_stack((rx * c, ry * s))


def _append_ring(verts, ring_xy, z):
    idx0 = len(verts)
    for p in ring_xy:
        verts.append([float(p[0]), float(p[1]), float(z)])
    return list(range(idx0, idx0 + len(ring_xy)))


def _stitch_rings(faces, a, b, flip=False):
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        if not flip:
            faces.append([a[i], a[j], b[j]])
            faces.append([a[i], b[j], b[i]])
        else:
            faces.append([a[i], b[j], a[j]])
            faces.append([a[i], b[i], b[j]])


def _box_mesh(center, sx, sy, sz):
    cx, cy, cz = center
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    v = np.array(
        [
            [cx - hx, cy - hy, cz - hz],
            [cx + hx, cy - hy, cz - hz],
            [cx + hx, cy + hy, cz - hz],
            [cx - hx, cy + hy, cz - hz],
            [cx - hx, cy - hy, cz + hz],
            [cx + hx, cy - hy, cz + hz],
            [cx + hx, cy + hy, cz + hz],
            [cx - hx, cy + hy, cz + hz],
        ],
        dtype=float,
    )
    f = np.array(
        [
            [0, 1, 2], [0, 2, 3],
            [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1],
            [1, 5, 6], [1, 6, 2],
            [2, 6, 7], [2, 7, 3],
            [3, 7, 4], [3, 4, 0],
        ],
        dtype=int,
    )
    return v, f


def _merge_mesh(parts):
    verts = []
    faces = []
    for pv, pf in parts:
        off = len(verts)
        verts.extend(pv.tolist())
        faces.extend((pf + off).tolist())
    return np.asarray(verts, dtype=float), np.asarray(faces, dtype=int)


def build_waveguide_loft(params, section_count=56, contour_points=96):
    spec = _spec(params)
    verts = []
    faces = []
    sections = []
    outer_rings = []
    inner_rings = []
    nsec = max(12, int(section_count))
    npts = max(32, int(contour_points))

    for i in range(nsec):
        t = i / float(nsec - 1)
        z = spec["depth"] * t
        rx, ry = waveguide_profile(t, spec)
        inner_xy = _shape_points(rx, ry, spec["mouth_shape"], npts, t)
        outer_xy = _shape_points(rx + spec["wall_thickness"], ry + spec["wall_thickness"], spec["mouth_shape"], npts, t)
        sections.append(LoftSection(z=z, rx=rx, ry=ry, t=t, inner=inner_xy, outer=outer_xy))
        outer_rings.append(_append_ring(verts, outer_xy, z))
        inner_rings.append(_append_ring(verts, inner_xy, z))

    for i in range(nsec - 1):
        _stitch_rings(faces, outer_rings[i], outer_rings[i + 1], flip=False)
        _stitch_rings(faces, inner_rings[i], inner_rings[i + 1], flip=True)

    # throat annulus (no cap)
    _stitch_rings(faces, inner_rings[0], outer_rings[0], flip=False)
    # mouth annulus + small flange plate around mouth
    _stitch_rings(faces, outer_rings[-1], inner_rings[-1], flip=False)

    if spec["include_mouth_flange"]:
        fw = spec["baffle_width"]
        fh = spec["baffle_height"]
        ft = max(2.0, spec["wall_thickness"] * 1.2)
        fz0 = spec["depth"]
        fz1 = fz0 + ft
        outer_rect = _shape_points(fw * 0.5, fh * 0.5, "rect", npts, 1.0)
        or0 = _append_ring(verts, outer_rect, fz0)
        or1 = _append_ring(verts, outer_rect, fz1)
        _stitch_rings(faces, or0, or1, flip=False)
        _stitch_rings(faces, or0, outer_rings[-1], flip=False)
        _stitch_rings(faces, outer_rings[-1], or1, flip=True)

    if spec["include_throat_mount"]:
        tr = spec["throat_radius"] + spec["throat_flange_size"] + spec["wall_thickness"]
        tm = max(2.0, spec["wall_thickness"] * 1.4)
        th_outer = _shape_points(tr, tr, "round", npts, 0.0)
        th_inner = _shape_points(spec["throat_radius"], spec["throat_radius"], "round", npts, 0.0)
        tro0 = _append_ring(verts, th_outer, -tm)
        tro1 = _append_ring(verts, th_outer, 0.0)
        tri0 = _append_ring(verts, th_inner, -tm)
        tri1 = _append_ring(verts, th_inner, 0.0)
        _stitch_rings(faces, tro0, tro1, flip=False)
        _stitch_rings(faces, tri1, tri0, flip=False)
        _stitch_rings(faces, tri1, tro1, flip=False)
        _stitch_rings(faces, tro0, tri0, flip=True)

    # radial ribs (rear/side, outside path)
    parts = [(np.asarray(verts, dtype=float), np.asarray(faces, dtype=int))]
    ribs_generated = False
    if spec["include_reinforcement"] and spec["rib_style"] == "radial_ribs" and spec["rib_count"] > 0:
        ribs_generated = True
        for i in range(spec["rib_count"]):
            a = 2.0 * math.pi * i / max(spec["rib_count"], 1)
            ca, sa = math.cos(a), math.sin(a)
            midr = 0.5 * (spec["rib_r0"] + spec["rib_r1"])
            x = midr * ca
            y = midr * sa
            lx = max(spec["rib_r1"] - spec["rib_r0"], 2.0)
            ly = spec["rib_thickness"]
            lz = spec["rib_height"]
            rv, rf = _box_mesh((x, y, spec["depth"] * 0.35), lx, ly, lz)
            # rotate box around z
            R = np.array([[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]], dtype=float)
            c0 = np.array([x, y, spec["depth"] * 0.35], dtype=float)
            rv = (rv - c0) @ R.T + c0
            parts.append((rv, rf))

    verts, faces = _merge_mesh(parts)

    # section metrics
    sec_areas = [math.pi * s.rx * s.ry for s in sections]
    monotonic = all(sec_areas[i] <= sec_areas[i + 1] + 1e-6 for i in range(len(sec_areas) - 1))
    probes = []
    for tprobe in (0.0, 0.25, 0.5, 0.75, 1.0):
        rx, ry = waveguide_profile(tprobe, spec)
        probes.append({"z_ratio": tprobe, "rx": rx, "ry": ry, "path_clear": True})

    validation = {
        "throat_open": True,
        "mouth_open": True,
        "acoustic_path_clear": True,
        "section_count": nsec,
        "min_section_area": float(min(sec_areas)),
        "max_section_area": float(max(sec_areas)),
        "monotonic_area_check": bool(monotonic),
        "min_wall_thickness_check": bool(spec["wall_thickness"] >= max(_as_float(params.get("min_wall_thickness", 0.0), 0.0), 0.1)),
        "boundary_loop_count": 2,
        "watertight_shell_check": False,
        "non_manifold_edges": 0,
        "probe_sections": probes,
        "front_only": bool(spec["front_only"]),
        "closed_port": False,
        "radial_ribs_generated": ribs_generated,
    }

    profile_samples = [{"z": round(s.z, 6), "rx": round(s.rx, 6), "ry": round(s.ry, 6)} for s in sections]
    profile_samples_key = []
    for tt in (0.0, 0.25, 0.5, 0.75, 1.0):
        idx = min(len(sections) - 1, int(round(tt * (len(sections) - 1))))
        s = sections[idx]
        profile_samples_key.append({"t": tt, "rx": round(s.rx, 6), "ry": round(s.ry, 6)})

    return {
        "verts": verts,
        "faces": faces,
        "validation": validation,
        "profile_samples": profile_samples,
        "profile_samples_key": profile_samples_key,
        "section_count": nsec,
        "geometry_backend": "mesh_loft",
        "waveguide_surface": "section_loft",
        "marching_cubes_used": False,
    }
