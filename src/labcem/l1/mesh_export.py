from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes


def extract_mesh(sdf_grid, level=0.0):
    verts, faces, normals, values = marching_cubes(np.asarray(sdf_grid, dtype=np.float32), level=level)
    return verts, faces, normals, values


def export_obj(verts, faces, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for v in verts:
            f.write("v {0} {1} {2}\n".format(v[0], v[1], v[2]))
        for tri in faces:
            f.write("f {0} {1} {2}\n".format(int(tri[0]) + 1, int(tri[1]) + 1, int(tri[2]) + 1))
    return p


def export_stl_ascii(verts, faces, path, name="labcem"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write("solid {0}\n".format(name))
        for tri in faces:
            a = verts[int(tri[0])]
            b = verts[int(tri[1])]
            c = verts[int(tri[2])]
            n = np.cross(b - a, c - a)
            norm = np.linalg.norm(n)
            if norm > 1e-9:
                n = n / norm
            else:
                n = np.array([0.0, 0.0, 0.0])
            f.write("  facet normal {0} {1} {2}\n".format(n[0], n[1], n[2]))
            f.write("    outer loop\n")
            f.write("      vertex {0} {1} {2}\n".format(a[0], a[1], a[2]))
            f.write("      vertex {0} {1} {2}\n".format(b[0], b[1], b[2]))
            f.write("      vertex {0} {1} {2}\n".format(c[0], c[1], c[2]))
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid {0}\n".format(name))
    return p
