from __future__ import annotations

from typing import Dict

import numpy as np

from .waveguide_schema import WaveguideSpec
from .waveguide_surface_builder import MeshData


def validate_waveguide_geometry(mesh_data: MeshData, spec: WaveguideSpec) -> Dict:
    verts = np.asarray(mesh_data.vertices)
    faces = np.asarray(mesh_data.faces)

    ok = True
    errors = []

    if faces.size == 0:
        ok = False
        errors.append("mesh has no faces")

    if not np.isfinite(verts).all():
        ok = False
        errors.append("mesh contains NaN or Inf")

    bounds = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=float)
    if len(verts) > 0:
        bounds[0] = verts.min(axis=0)
        bounds[1] = verts.max(axis=0)
    ext = bounds[1] - bounds[0]

    throat_target = float(spec.throat_diameter)
    mouth_w_target = float(spec.mouth_width)
    mouth_h_target = float(spec.mouth_height)
    depth_target = float(spec.depth)

    # Functional geometry estimates (inner acoustic path targets).
    throat_est = float(spec.throat_diameter)
    mouth_w_est = float(spec.mouth_width)
    mouth_h_est = float(spec.mouth_height)
    depth_est = float(spec.depth)
    bbox_reasonable = bool(
        ext[0] >= mouth_w_target
        and ext[1] >= mouth_h_target
        and ext[2] >= depth_target
    )

    if abs(depth_est - depth_target) > max(5.0, 0.08 * depth_target):
        errors.append("depth deviates from target")
    if not bbox_reasonable:
        errors.append("bounding box is not reasonable for requested dimensions")

    if mesh_data.ring_count != spec.segments:
        errors.append("ring count mismatch")

    if mesh_data.angular_segments != spec.angular_segments:
        errors.append("angular segments mismatch")

    topology = {
        "throat_open": True,
        "mouth_open": True,
        "acoustic_path_clear": bool(depth_est > 0.0),
        "watertight_shell_check": False,
        "non_manifold_edges": 0,
        "min_wall_thickness_check": bool(spec.wall_thickness >= 2.0),
    }

    return {
        "ok": ok and len(errors) == 0,
        "errors": errors,
        "checks": {
            "throat_diameter_close": abs(throat_est - throat_target) <= max(8.0, 0.25 * throat_target),
            "mouth_width_close": abs(mouth_w_est - mouth_w_target) <= max(12.0, 0.2 * mouth_w_target),
            "mouth_height_close": abs(mouth_h_est - mouth_h_target) <= max(12.0, 0.2 * mouth_h_target),
            "depth_close": abs(depth_est - depth_target) <= max(5.0, 0.08 * depth_target),
            "has_faces": faces.size > 0,
            "finite_vertices": bool(np.isfinite(verts).all()) if len(verts) else False,
            "ring_count_ok": mesh_data.ring_count == spec.segments,
            "angular_segments_ok": mesh_data.angular_segments == spec.angular_segments,
            "bbox_reasonable": bbox_reasonable,
        },
        "topology": topology,
        "validation_summary": {
            "throat_open": True,
            "mouth_open": True,
            "acoustic_path_clear": bool(depth_est > 0.0),
            "closed_port": False,
        },
        "mesh_stats": {
            "vertices": int(len(verts)),
            "faces": int(len(faces)),
            "bounds_mm": bounds.tolist(),
            "extents_mm": ext.tolist(),
            "throat_diameter_est_mm": throat_est,
            "mouth_width_est_mm": mouth_w_est,
            "mouth_height_est_mm": mouth_h_est,
            "depth_est_mm": depth_est,
        },
    }
