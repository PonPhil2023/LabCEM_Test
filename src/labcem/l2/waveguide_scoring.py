def score_waveguide_candidate(requirement, target, profile):
    pts = profile.points
    areas = [p["area"] for p in pts]
    exp = [p["local_expansion_rate"] for p in pts[1:]]
    mouth_w = pts[-1]["rx"] * 2.0
    mouth_h = pts[-1]["ry"] * 2.0
    depth = pts[-1]["z"]

    bw_score = max(0.0, 100.0 - abs(mouth_w - target.mouth_width_mm) * 0.6 - abs(mouth_h - target.mouth_height_mm) * 0.6)
    dir_score = max(0.0, 100.0 - abs((mouth_w / max(mouth_h, 1e-6)) - target.aspect_ratio) * 25.0)
    smoothness = max(0.0, 100.0 - (max(exp) - min(exp)) * 120.0) if exp else 80.0
    manufact = 100.0 if requirement.min_wall_thickness_mm >= 2.0 else 70.0
    geom_valid = 100.0 if all(areas[i] <= areas[i + 1] + 1e-6 for i in range(len(areas) - 1)) else 40.0
    compact_pen = max(0.0, (depth - requirement.max_depth_mm) * 1.2)

    total = (
        0.24 * bw_score
        + 0.24 * dir_score
        + 0.18 * smoothness
        + 0.14 * manufact
        + 0.14 * geom_valid
        - 0.06 * compact_pen
    )
    return {
        "bandwidth_score": round(bw_score, 2),
        "directivity_score": round(dir_score, 2),
        "smoothness_score": round(smoothness, 2),
        "manufacturability_score": round(manufact, 2),
        "geometry_validity_score": round(geom_valid, 2),
        "compactness_penalty": round(compact_pen, 2),
        "total_score": round(total, 2),
        "evaluation_mode": "rule_based_estimate",
    }

