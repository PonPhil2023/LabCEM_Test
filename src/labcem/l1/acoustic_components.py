from labcem.l1.sdf_primitives import horn_sdf


def waveguide_component(throat_radius=6.0, mouth_radius=28.0, depth=30.0):
    return {
        "type": "waveguide",
        "sdf": lambda x, y, z: horn_sdf(x, y, z, throat_radius=throat_radius, mouth_radius=mouth_radius, depth=depth),
    }
