ACOUSTIC_TEMPLATES = {
    "ath_waveguide": {
        "intent": "create_ath_waveguide",
        "backend": "cadquery",
        "shape": "waveguide",
        "profile": "oblate_spheroid",
        "throat_radius": 12.7,
        "mouth_radius": 60.0,
        "depth": 35.0,
        "wall_thickness": 3.0,
        "operations": [
            {"op": "shell", "thickness": 3.0},
            {"op": "fillet_edges", "radius": 5.0},
        ],
    },
    "acoustic_waveguide": {
        "intent": "create_acoustic_waveguide",
        "backend": "cadquery",
        "shape": "waveguide",
        "throat_radius": 12.7,
        "mouth_radius": 60.0,
        "depth": 35.0,
        "wall_thickness": 3.0,
        "operations": [
            {"op": "shell", "thickness": 3.0},
            {"op": "fillet_edges", "radius": 4.0},
        ],
    },
    "acoustic_horn": {
        "intent": "create_acoustic_horn",
        "backend": "sdf",
        "shape": "horn",
        "throat_radius": 10.0,
        "mouth_radius": 45.0,
        "depth": 55.0,
        "operations": [{"op": "offset", "delta": -0.5}],
    },
}


def get_acoustic_template(name):
    return ACOUSTIC_TEMPLATES.get(name)
