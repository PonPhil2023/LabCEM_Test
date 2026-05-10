import numpy as np


class SDFGrid:
    def __init__(self, resolution=32, span=50.0):
        self.resolution = int(max(12, resolution))
        self.span = float(span)
        self.axis = np.linspace(-self.span / 2.0, self.span / 2.0, self.resolution)
        self.values = np.full((self.resolution, self.resolution, self.resolution), 1e6, dtype=np.float32)

    def sample(self, sdf_fn):
        for ix, x in enumerate(self.axis):
            for iy, y in enumerate(self.axis):
                for iz, z in enumerate(self.axis):
                    self.values[ix, iy, iz] = float(sdf_fn(float(x), float(y), float(z)))
        return self

    def occupancy(self):
        return self.values <= 0.0

    def narrow_band(self, band=1.5):
        return np.abs(self.values) <= float(band)

    def voxel_indices(self):
        inside = np.argwhere(self.occupancy())
        return [tuple(int(v) for v in xyz) for xyz in inside]
