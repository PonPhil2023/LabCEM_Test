from copy import deepcopy

from labcem.l2.acoustic_target import acoustic_target_to_dict, build_acoustic_target
from labcem.l2.requirement_parser import parse_waveguide_requirement, requirement_to_dict
from labcem.l2.waveguide_optimizer import optimize_waveguide, serialize_candidates


def _legacy_score_candidate(c):
    p = c["parameters"]
    wall = float(p["wall_thickness"]["value"])
    depth = float(p["depth"]["value"])
    mouth_w = float(p["mouth_width"]["value"])
    mouth_h = float(p["mouth_height"]["value"])
    acoustic = min(100.0, 40.0 + 0.15 * mouth_w + 0.08 * mouth_h + 0.2 * depth)
    manufact = 100.0 - max(0.0, (3.0 - wall) * 60.0)
    smooth = max(0.0, 100.0 - abs(depth - 0.45 * mouth_w) * 1.2)
    mesh_validity = 100.0 if wall >= 2.5 else 65.0
    total = 0.35 * acoustic + 0.25 * manufact + 0.2 * smooth + 0.2 * mesh_validity
    return {
        "acoustic_score": round(acoustic, 2),
        "manufacturability_score": round(manufact, 2),
        "smoothness_score": round(smooth, 2),
        "mesh_validity_score": round(mesh_validity, 2),
        "total_score": round(total, 2),
    }


def _legacy_optimize(plan):
    base = deepcopy(plan)
    params = base["parameters"]
    seeds = [
        {"waveguide_type": "oblate_spheroid", "curve_blend": 0.30, "depth_scale": 1.00},
        {"waveguide_type": "exponential", "curve_blend": 0.55, "depth_scale": 1.08},
        {"waveguide_type": "tractrix", "curve_blend": 0.20, "depth_scale": 0.95},
        {"waveguide_type": "compound", "curve_blend": 0.42, "depth_scale": 1.03},
    ]
    out = []
    base_depth = float(params["depth"]["value"])
    for i, s in enumerate(seeds, 1):
        c = deepcopy(base)
        c["candidate_id"] = f"C{i}"
        c["parameters"]["waveguide_type"]["value"] = s["waveguide_type"]
        c["parameters"].setdefault("curve_blend", {"value": 0.35, "unit": "ratio", "required": False})
        c["parameters"]["curve_blend"]["value"] = s["curve_blend"]
        c["parameters"]["depth"]["value"] = round(base_depth * s["depth_scale"], 3)
        c["scores"] = _legacy_score_candidate(c)
        out.append(c)
    out.sort(key=lambda x: x["scores"]["total_score"], reverse=True)
    return out, out[0]


def optimize_candidates(plan):
    if plan.get("shape") != "waveguide":
        return _legacy_optimize(plan)

    req = parse_waveguide_requirement(plan.get("spec", ""))
    target = build_acoustic_target(req)
    candidates, best = optimize_waveguide(req, target, method="grid_search")

    plan["cem_mode"] = "target_driven_waveguide"
    plan["input_requirements"] = requirement_to_dict(req)
    plan["acoustic_target"] = acoustic_target_to_dict(target)
    plan["candidate_scores"] = serialize_candidates(candidates, top_k=8)
    selected_profile_type = "tritonia_m" if str(req.preferred_profile_type) == "tritonia_m" else best["profile_type"]
    plan["selected_candidate"] = {
        "candidate_id": best["candidate_id"],
        "profile_type": selected_profile_type,
        "scores": best["scores"],
    }

    best_profile = best["profile"]
    params = plan["parameters"]
    params["mouth_width"]["value"] = round(float(target.mouth_width_mm), 4)
    params["mouth_height"]["value"] = round(float(target.mouth_height_mm), 4)
    params["depth"]["value"] = round(float(target.depth_estimate_mm), 4)
    if str(req.preferred_profile_type) == "tritonia_m":
        params["waveguide_type"]["value"] = "tritonia_m"
    else:
        params["waveguide_type"]["value"] = str(best_profile.profile_type)
    params.setdefault("curve_blend", {"value": 0.35, "unit": "ratio", "required": False})
    params["curve_blend"]["value"] = 0.35
    params.setdefault("throat_diameter", {"value": float(req.throat_diameter_mm), "unit": "mm", "required": True})
    params["throat_diameter"]["value"] = float(req.throat_diameter_mm)

    fake_candidates = []
    for c in candidates[:4]:
        cc = deepcopy(plan)
        cc["candidate_id"] = c["candidate_id"]
        cc["scores"] = c["scores"]
        if str(req.preferred_profile_type) == "tritonia_m":
            cc["parameters"]["waveguide_type"]["value"] = "tritonia_m"
        else:
            cc["parameters"]["waveguide_type"]["value"] = c["profile_type"]
        fake_candidates.append(cc)
    best_fake = fake_candidates[0] if fake_candidates else deepcopy(plan)
    best_fake["scores"] = best["scores"]
    best_fake["candidate_id"] = best["candidate_id"]
    if str(req.preferred_profile_type) == "tritonia_m":
        best_fake["parameters"]["waveguide_type"]["value"] = "tritonia_m"
    else:
        best_fake["parameters"]["waveguide_type"]["value"] = best["profile_type"]
    return fake_candidates or [best_fake], best_fake
