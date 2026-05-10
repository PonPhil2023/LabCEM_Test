from pathlib import Path


def _probe_open(grid_vals, z_index, center_x, center_y, radius=2):
    h, w, d = grid_vals.shape
    cnt = 0
    open_cnt = 0
    z = max(0, min(d - 1, z_index))
    for i in range(max(0, center_x - radius), min(h, center_x + radius + 1)):
        for j in range(max(0, center_y - radius), min(w, center_y + radius + 1)):
            cnt += 1
            if grid_vals[i, j, z] > 0.0:
                open_cnt += 1
    return (open_cnt / max(cnt, 1)) > 0.65


def validate_mesh(grid, params, stl_path=None):
    vals = grid.values
    n = vals.shape[0]
    c = n // 2

    throat_open = _probe_open(vals, 1, c, c)
    mouth_open = _probe_open(vals, n - 2, c, c, radius=4)

    wall_t = float(params.get("wall_thickness", 0.0) or 0.0)
    min_wall = float(params.get("min_wall_thickness", 0.0) or 0.0)

    watertight = None
    non_manifold = None
    if stl_path:
        try:
            import trimesh

            mesh = trimesh.load_mesh(str(stl_path))
            watertight = bool(mesh.is_watertight)
            non_manifold = not watertight
        except Exception:
            watertight = None
            non_manifold = None

    export_ready = bool(throat_open and mouth_open and (wall_t >= max(min_wall, 0.1)))

    return {
        "topology": {
            "throat_open": bool(throat_open),
            "mouth_open": bool(mouth_open),
            "watertight": watertight,
            "non_manifold": non_manifold,
        },
        "checks": {
            "min_wall_thickness": min_wall,
            "wall_thickness": wall_t,
            "wall_ok": wall_t >= max(min_wall, 0.1),
            "export_ready": export_ready,
        },
    }
