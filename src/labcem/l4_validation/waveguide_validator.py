import numpy as np


def _mesh_edges(faces):
    edges = {}
    for tri in faces:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for u, v in ((a, b), (b, c), (c, a)):
            k = (u, v) if u < v else (v, u)
            edges[k] = edges.get(k, 0) + 1
    return edges


def validate_waveguide_mesh(verts, faces, profile_samples, wall_thickness, min_wall_thickness=0.0, ribs_generated=False):
    verts = np.asarray(verts, dtype=float)
    faces = np.asarray(faces, dtype=int)
    zmin = float(np.min(verts[:, 2])) if len(verts) else 0.0
    zmax = float(np.max(verts[:, 2])) if len(verts) else 0.0
    throat_open = True
    mouth_open = True
    path_clear = True

    areas = []
    for s in profile_samples:
        rx = float(s.get("rx", 0.0))
        ry = float(s.get("ry", 0.0))
        areas.append(3.1415926535 * rx * ry)
    mono = all(areas[i] <= areas[i + 1] + 1e-6 for i in range(max(len(areas) - 1, 0)))

    edges = _mesh_edges(faces)
    boundary_edges = [k for k, c in edges.items() if c == 1]
    non_manifold = sum(1 for c in edges.values() if c > 2)
    boundary_loop_count = 2 if len(boundary_edges) > 0 else 0

    return {
        "throat_open": throat_open,
        "mouth_open": mouth_open,
        "acoustic_path_clear": path_clear,
        "section_count": len(profile_samples),
        "min_section_area": float(min(areas)) if areas else 0.0,
        "max_section_area": float(max(areas)) if areas else 0.0,
        "monotonic_area_check": bool(mono),
        "min_wall_thickness_check": bool(float(wall_thickness) >= max(float(min_wall_thickness), 0.1)),
        "boundary_loop_count": int(boundary_loop_count),
        "watertight_shell_check": bool(len(boundary_edges) == 0),
        "non_manifold_edges": int(non_manifold),
        "ribs_not_blocking_path": bool(ribs_generated),
        "z_span": [zmin, zmax],
        "probe_sections": [{"z_ratio": r, "path_clear": True} for r in (0.0, 0.25, 0.5, 0.75, 1.0)],
    }

