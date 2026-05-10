from labcem.l1.geometry import GeometryObject, cylinder


def _as_float(value, default):
    return float(default if value is None else value)


def build_cad_geometry(params):
    shape = params.get("shape", "cylinder")
    if shape in ("waveguide", "horn"):
        return GeometryObject(
            kind="waveguide",
            params={
                "throat_radius": _as_float(params.get("throat_radius", 12.7), 12.7),
                "mouth_radius": _as_float(params.get("mouth_radius", 60.0), 60.0),
                "depth": _as_float(params.get("depth", 35.0), 35.0),
                "wall_thickness": _as_float(params.get("wall_thickness", 3.0), 3.0),
                "waveguide_type": str(params.get("waveguide_type", "oblate_spheroid")),
                "frequency_band": str(params.get("frequency_band", "")),
                "throat_flange_shape": str(params.get("throat_flange_shape", "round")),
                "throat_flange_size": _as_float(params.get("throat_flange_size", 0.0), 0.0),
                "mouth_flange_shape": str(params.get("mouth_flange_shape", "round")),
                "mouth_flange_size": _as_float(params.get("mouth_flange_size", 0.0), 0.0),
                "mouth_shape": str(params.get("mouth_shape", "ellipse")),
                "mouth_width": _as_float(params.get("mouth_width", _as_float(params.get("mouth_radius", 60.0), 60.0) * 2.0), 120.0),
                "mouth_height": _as_float(params.get("mouth_height", _as_float(params.get("mouth_radius", 60.0), 60.0) * 2.0), 90.0),
                "roundover_radius": _as_float(params.get("roundover_radius", 8.0), 8.0),
                "throat_angle": _as_float(params.get("throat_angle", 10.0), 10.0),
                "term_s_base": _as_float(params.get("term_s_base", 0.7), 0.7),
                "term_s_cos2": _as_float(params.get("term_s_cos2", 0.2), 0.2),
                "term_n": _as_float(params.get("term_n", 3.7), 3.7),
                "term_q": _as_float(params.get("term_q", 0.992), 0.992),
                "morph_rate": _as_float(params.get("morph_rate", 3.0), 3.0),
                "morph_corner_radius": _as_float(params.get("morph_corner_radius", 18.0), 18.0),
                "front_only": bool(params.get("front_only", True)),
                "geometry_mode": "ath_open_front_shell",
                "reinforcement_style": str(params.get("reinforcement_style", "radial_ribs")),
                "reinforcement_count": int(_as_float(params.get("reinforcement_count", 6), 6)),
                "reinforcement_thickness": _as_float(params.get("reinforcement_thickness", 2.5), 2.5),
                "reinforcement_height": _as_float(params.get("reinforcement_height", 8.0), 8.0),
                "reinforcement_start_radius": _as_float(params.get("reinforcement_start_radius", 18.0), 18.0),
                "reinforcement_end_radius": _as_float(params.get("reinforcement_end_radius", 58.0), 58.0),
            },
        )
    if shape == "hex_bolt":
        return GeometryObject(
            kind="hex_bolt",
            params={
                "shaft_radius": _as_float(params.get("shaft_radius", 2.0), 2.0),
                "shaft_length": _as_float(params.get("shaft_length", 26.0), 26.0),
                "head_radius": _as_float(params.get("head_radius", 4.0), 4.0),
                "head_height": _as_float(params.get("head_height", 3.0), 3.0),
            },
        )
    return cylinder(
        radius=_as_float(params.get("radius", 10.0), 10.0),
        height=_as_float(params.get("height", 40.0), 40.0),
    )
