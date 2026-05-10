from copy import deepcopy

from labcem.l2.waveguide_curve_solver import profile_to_dict, solve_waveguide_curve
from labcem.l2.waveguide_scoring import score_waveguide_candidate


def optimize_waveguide(requirement, target, method="grid_search"):
    profile_types = ["conical", "exponential", "bezier", "os_like", "superellipse_loft"]
    candidates = []
    cid = 1
    for ptype in profile_types:
        for dscale in (0.9, 1.0, 1.08):
            t = deepcopy(target)
            t.depth_estimate_mm = min(requirement.max_depth_mm, max(20.0, t.depth_estimate_mm * dscale))
            prof = solve_waveguide_curve(requirement, t, profile_type=ptype, section_count=56)
            sc = score_waveguide_candidate(requirement, t, prof)
            candidates.append(
                {
                    "candidate_id": f"WG{cid}",
                    "profile_type": ptype,
                    "target": t,
                    "profile": prof,
                    "scores": sc,
                    "optimizer_method": method,
                }
            )
            cid += 1

    candidates.sort(key=lambda c: c["scores"]["total_score"], reverse=True)
    best = candidates[0]
    return candidates, best


def serialize_candidates(candidates, top_k=8):
    out = []
    for c in candidates[:top_k]:
        out.append(
            {
                "candidate_id": c["candidate_id"],
                "profile_type": c["profile_type"],
                "scores": c["scores"],
                "target_depth_mm": round(float(c["target"].depth_estimate_mm), 3),
            }
        )
    return out


def selected_candidate_payload(best):
    return {
        "candidate_id": best["candidate_id"],
        "profile_type": best["profile_type"],
        "scores": best["scores"],
        "profile": profile_to_dict(best["profile"]),
    }

