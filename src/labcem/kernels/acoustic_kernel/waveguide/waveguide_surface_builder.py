from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import trimesh

from .cross_section_morph import ring_params_at_t, superellipse_points
from .waveguide_schema import WaveguideSpec


@dataclass
class MeshData:
    vertices: np.ndarray
    faces: np.ndarray
    ring_count: int
    angular_segments: int


def _connect_rings(faces: List[List[int]], ring_a: np.ndarray, ring_b: np.ndarray) -> None:
    n = len(ring_a)
    for j in range(n):
        jn = (j + 1) % n
        a0 = int(ring_a[j])
        a1 = int(ring_a[jn])
        b0 = int(ring_b[j])
        b1 = int(ring_b[jn])
        faces.append([a0, b0, b1])
        faces.append([a0, b1, a1])


def _cap_ring(faces: List[List[int]], ring: np.ndarray, center_idx: int, invert: bool = False) -> None:
    n = len(ring)
    for j in range(n):
        jn = (j + 1) % n
        if invert:
            faces.append([center_idx, int(ring[jn]), int(ring[j])])
        else:
            faces.append([center_idx, int(ring[j]), int(ring[jn])])


def _build_shell(spec: WaveguideSpec) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    vertices: List[List[float]] = []
    faces: List[List[int]] = []

    ring_indices_inner: List[np.ndarray] = []
    ring_indices_outer: List[np.ndarray] = []

    m = spec.angular_segments
    seg = spec.segments
    adapter = spec.throat_adapter_depth
    depth_total = max(1e-6, spec.depth)

    for i in range(seg):
        t = i / (seg - 1)
        z = adapter + t * depth_total
        width_t, height_t, exponent_t, _p = ring_params_at_t(
            t=t,
            family=spec.family,
            throat_diameter=spec.throat_diameter,
            mouth_width=spec.mouth_width,
            mouth_height=spec.mouth_height,
            profile_power=spec.profile_power,
            morph_rate=spec.morph_rate,
        )
        inner_ring = superellipse_points(width_t, height_t, exponent_t, z, m)
        outer_ring = superellipse_points(width_t + 2.0 * spec.wall_thickness, height_t + 2.0 * spec.wall_thickness, exponent_t, z, m)

        inner_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
        vertices.extend(inner_ring.tolist())
        outer_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
        vertices.extend(outer_ring.tolist())

        ring_indices_inner.append(inner_idx)
        ring_indices_outer.append(outer_idx)

    # Throat adapter rings (circular-ish by exponent 2)
    throat_w = spec.throat_diameter
    throat_outer_w = spec.throat_diameter + 2.0 * spec.wall_thickness
    throat0_inner = superellipse_points(throat_w, throat_w, 2.0, 0.0, m)
    throat0_outer = superellipse_points(throat_outer_w, throat_outer_w, 2.0, 0.0, m)
    throat1_inner = superellipse_points(throat_w, throat_w, 2.0, adapter, m)
    throat1_outer = superellipse_points(throat_outer_w, throat_outer_w, 2.0, adapter, m)

    throat0_inner_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(throat0_inner.tolist())
    throat0_outer_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(throat0_outer.tolist())
    throat1_inner_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(throat1_inner.tolist())
    throat1_outer_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(throat1_outer.tolist())

    # Join throat adapter tube to first morph ring
    _connect_rings(faces, throat0_outer_idx, throat1_outer_idx)
    _connect_rings(faces, throat1_outer_idx, ring_indices_outer[0])
    _connect_rings(faces, ring_indices_inner[0], throat1_inner_idx)
    _connect_rings(faces, throat1_inner_idx, throat0_inner_idx)

    # Side walls along depth
    for i in range(seg - 1):
        _connect_rings(faces, ring_indices_outer[i], ring_indices_outer[i + 1])
        _connect_rings(faces, ring_indices_inner[i + 1], ring_indices_inner[i])

    # Mouth roundover transition rings (outer only soft transition)
    mouth_z = adapter + depth_total
    transition_count = 4
    prev_outer = ring_indices_outer[-1]
    for k in range(1, transition_count + 1):
        u = k / transition_count
        w = spec.mouth_width + 2.0 * spec.wall_thickness + 2.0 * spec.roundover_radius * (u * 0.35)
        h = spec.mouth_height + 2.0 * spec.wall_thickness + 2.0 * spec.roundover_radius * (u * 0.35)
        z = mouth_z + spec.roundover_radius * (u * 0.25)
        tr = superellipse_points(w, h, 8.0, z, m)
        tr_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
        vertices.extend(tr.tolist())
        _connect_rings(faces, prev_outer, tr_idx)
        prev_outer = tr_idx

    # Flange frame (rectangular-ish superellipse) and cap ring
    flange_w = spec.mouth_width + 2.0 * spec.wall_thickness + 2.0 * spec.flange_margin
    flange_h = spec.mouth_height + 2.0 * spec.wall_thickness + 2.0 * spec.flange_margin
    flange_z0 = mouth_z
    flange_z1 = mouth_z + max(0.0, spec.flange_thickness)
    flange0 = superellipse_points(flange_w, flange_h, 10.0, flange_z0, m)
    flange1 = superellipse_points(flange_w, flange_h, 10.0, flange_z1, m)
    flange0_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(flange0.tolist())
    flange1_idx = np.arange(len(vertices), len(vertices) + m, dtype=np.int32)
    vertices.extend(flange1.tolist())

    _connect_rings(faces, prev_outer, flange0_idx)
    _connect_rings(faces, flange0_idx, flange1_idx)

    # Throat rear face annulus cap
    center_back_idx = len(vertices)
    vertices.append([0.0, 0.0, 0.0])
    _cap_ring(faces, throat0_outer_idx, center_back_idx, invert=True)
    _cap_ring(faces, throat0_inner_idx, center_back_idx, invert=False)

    # Mouth front flange cap annulus, keep central opening by bridging outer flange to mouth inner
    _connect_rings(faces, ring_indices_inner[-1], flange1_idx)

    return np.asarray(vertices, dtype=np.float64), np.asarray(faces, dtype=np.int32), {
        "inner_start": throat0_inner_idx,
        "inner_end": ring_indices_inner[-1],
        "outer_end": flange1_idx,
    }


def build_ath_like_waveguide_mesh(spec: WaveguideSpec) -> MeshData:
    vertices, faces, _meta = _build_shell(spec)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    try:
        mesh.remove_unreferenced_vertices()
    except Exception:
        pass
    return MeshData(
        vertices=np.asarray(mesh.vertices, dtype=np.float64),
        faces=np.asarray(mesh.faces, dtype=np.int32),
        ring_count=int(spec.segments),
        angular_segments=int(spec.angular_segments),
    )
