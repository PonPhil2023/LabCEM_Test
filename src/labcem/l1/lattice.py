import math


def gyroid(x, y, z):
    return math.sin(x) * math.cos(y) + math.sin(y) * math.cos(z) + math.sin(z) * math.cos(x)


def schwarz_p(x, y, z):
    return math.cos(x) + math.cos(y) + math.cos(z)


def cubic_lattice(x, y, z, cell=1.0):
    c = max(cell, 1e-6)
    fx = abs((x / c) - round(x / c))
    fy = abs((y / c) - round(y / c))
    fz = abs((z / c) - round(z / c))
    return min(fx, fy, fz)


def gradient_lattice_density(z, z_min, z_max, d0=0.2, d1=0.6):
    if z_max <= z_min:
        return d0
    t = (z - z_min) / (z_max - z_min)
    return d0 + (d1 - d0) * max(0.0, min(1.0, t))
