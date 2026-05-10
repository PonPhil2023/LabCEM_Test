import math
import numpy as np


def cylinder_sdf(x, y, z, radius, height):
    radial = math.sqrt(x * x + y * y) - radius
    axial = abs(z) - (height / 2.0)
    return max(radial, axial)


def sphere_sdf(x, y, z, radius):
    return math.sqrt(x * x + y * y + z * z) - radius


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


def sample_sdf_grid(shape, resolution, params):
    res = max(12, int(resolution))

    if shape == "torus":
        major = float(params.get("major_radius", 22.0))
        minor = float(params.get("minor_radius", 7.0))
        span = (major + minor) * 2.4
    elif shape == "hex_bolt":
        shaft_radius = float(params.get("shaft_radius", 2.0))
        shaft_length = float(params.get("shaft_length", 26.0))
        head_radius = float(params.get("head_radius", 4.0))
        head_height = float(params.get("head_height", 3.0))
        span = max(head_radius * 3.0, (shaft_length + head_height) * 1.6)
    elif shape == "sphere":
        radius = float(params.get("radius", 10.0))
        span = radius * 2.6
    else:
        radius = float(params.get("radius", 10.0))
        height = float(params.get("height", 40.0))
        span = max(radius * 2.4, height * 1.2)

    axis = np.linspace(-span / 2.0, span / 2.0, res)
    grid = np.empty((res, res, res), dtype=np.float32)

    for ix, x in enumerate(axis):
        for iy, y in enumerate(axis):
            for iz, z in enumerate(axis):
                xf = float(x)
                yf = float(y)
                zf = float(z)
                if shape == "torus":
                    grid[ix, iy, iz] = torus_sdf(xf, yf, zf, major, minor)
                elif shape == "hex_bolt":
                    grid[ix, iy, iz] = hex_bolt_sdf(xf, yf, zf, shaft_radius, shaft_length, head_radius, head_height)
                elif shape == "sphere":
                    grid[ix, iy, iz] = sphere_sdf(xf, yf, zf, radius)
                else:
                    grid[ix, iy, iz] = cylinder_sdf(xf, yf, zf, radius, height)

    return {"resolution": res, "span": span, "axis": axis, "sdf_grid": grid}


def voxels_from_sdf_grid(sdf_grid):
    inside = np.argwhere(sdf_grid <= 0.0)
    return [tuple(int(v) for v in xyz) for xyz in inside]


def apply_lattice(voxels, interval):
    keep = []
    n = max(2, int(interval))
    for ix, iy, iz in voxels:
        if (ix % n == 0) or (iy % n == 0) or (iz % n == 0):
            keep.append((ix, iy, iz))
    return keep
