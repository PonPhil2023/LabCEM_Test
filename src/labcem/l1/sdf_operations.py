import math


def union(a, b):
    return min(a, b)


def subtract(a, b):
    return max(a, -b)


def intersect(a, b):
    return max(a, b)


def smooth_union(a, b, k=1.0):
    h = max(k - abs(a - b), 0.0) / max(k, 1e-6)
    return min(a, b) - h * h * h * k * (1.0 / 6.0)


def offset(d, delta):
    return d - delta


def shell(d, thickness):
    return abs(d) - thickness
