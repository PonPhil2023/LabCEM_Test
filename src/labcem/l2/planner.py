import copy
import json
import re
from pathlib import Path

from labcem.l3_library.acoustic_library import get_acoustic_template
from labcem.l2.acoustic_rule_checker import check_waveguide_rules
from labcem.l2.design_optimizer import optimize_candidates
from labcem.l2.requirement_parser import is_target_waveguide_prompt

ATH_WAVEGUIDE_SCHEMA = {
    "frequency_band": {"required": True, "unit": "Hz", "default": None},
    "waveguide_type": {"required": False, "unit": "enum", "default": None},
    "throat_angle": {"required": False, "unit": "deg", "default": 10.0},
    "throat_diameter": {"required": True, "unit": "mm", "default": None},
    "mouth_shape": {"required": True, "unit": "enum", "default": None},
    "mouth_width": {"required": True, "unit": "mm", "default": None},
    "mouth_height": {"required": True, "unit": "mm", "default": None},
    "depth": {"required": True, "unit": "mm", "default": 35.0},
    "roundover_radius": {"required": False, "unit": "mm", "default": 8.0},
    "throat_flange_shape": {"required": False, "unit": "enum", "default": "round"},
    "throat_flange_size": {"required": False, "unit": "mm", "default": 0.0},
    "mouth_flange_shape": {"required": False, "unit": "enum", "default": "round"},
    "mouth_flange_size": {"required": False, "unit": "mm", "default": 0.0},
    "wall_thickness": {"required": True, "unit": "mm", "default": None},
    "term_s_base": {"required": False, "unit": "ratio", "default": 0.7},
    "term_s_cos2": {"required": False, "unit": "ratio", "default": 0.2},
    "term_n": {"required": False, "unit": "ratio", "default": 3.7},
    "term_q": {"required": False, "unit": "ratio", "default": 0.992},
    "morph_rate": {"required": False, "unit": "ratio", "default": 3.0},
    "morph_corner_radius": {"required": False, "unit": "mm", "default": 18.0},
    "baffle_width": {"required": False, "unit": "mm", "default": 180.0},
    "baffle_height": {"required": False, "unit": "mm", "default": 180.0},
    "baffle_thickness": {"required": False, "unit": "mm", "default": 6.0},
    "screw_count": {"required": False, "unit": "count", "default": 4},
    "screw_diameter": {"required": False, "unit": "mm", "default": 4.2},
    "screw_spacing": {"required": False, "unit": "mm", "default": 150.0},
    "manufacturing_method": {"required": False, "unit": "enum", "default": "FDM"},
    "min_wall_thickness": {"required": False, "unit": "mm", "default": 3.0},
    "reinforcement_style": {"required": False, "unit": "enum", "default": "radial_ribs"},
    "reinforcement_count": {"required": False, "unit": "count", "default": 6},
    "reinforcement_thickness": {"required": False, "unit": "mm", "default": 2.5},
    "reinforcement_height": {"required": False, "unit": "mm", "default": 8.0},
    "reinforcement_start_radius": {"required": False, "unit": "mm", "default": 18.0},
    "reinforcement_end_radius": {"required": False, "unit": "mm", "default": 58.0},
}

QUESTION_ORDER = [
    "frequency_band",
    "throat_diameter",
    "mouth_shape",
    "mouth_width",
    "mouth_height",
    "depth",
    "throat_flange_shape",
    "throat_flange_size",
    "mouth_flange_shape",
    "mouth_flange_size",
    "wall_thickness",
]


def _extract_mm_values(text):
    vals = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*mm", text, flags=re.IGNORECASE):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            continue
    return vals


def _extract_throat_diameter_mm(text):
    patterns = [
        r"throat[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"喉口[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"猴口[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"喉口[^0-9]{0,20}直徑[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm",
        r"猴口[^0-9]{0,20}直徑[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None


def _extract_mouth_wh_mm(text):
    patterns = [
        r"mouth[^0-9]{0,20}(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm",
        r"mouth[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm",
        r"出口[^0-9]{0,20}(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm",
        r"出口[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm",
        r"出口[^0-9]{0,20}寬[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm[^0-9]{0,10}高[^0-9]{0,10}(\d+(?:\.\d+)?)\s*mm",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1)), float(m.group(2))
            except Exception:
                pass
    return None, None


def _extract_depth_mm(text):
    patterns = [
        r"depth[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"深度[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None


def _extract_wall_mm(text):
    patterns = [
        r"wall[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"壁厚[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
        r"薄殼[^0-9]{0,20}(\d+(?:\.\d+)?)\s*mm",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None


def _extract_hz_range(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k)?\s*hz\s*[-~to]{1,3}\s*(\d+(?:\.\d+)?)\s*(k)?\s*hz", text, flags=re.IGNORECASE)
    if m:
        a = float(m.group(1)) * (1000.0 if m.group(2) else 1.0)
        b = float(m.group(3)) * (1000.0 if m.group(4) else 1.0)
        return "{0:.0f}-{1:.0f}".format(min(a, b), max(a, b))
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*(k)?\s*hz", text, flags=re.IGNORECASE)
    if m2:
        mult = 1000.0 if m2.group(3) else 1.0
        a = float(m2.group(1)) * mult
        b = float(m2.group(2)) * mult
        return "{0:.0f}-{1:.0f}".format(min(a, b), max(a, b))
    return None


def _infer_waveguide_type(text):
    t = text.lower()
    if "tritonia" in t:
        return "tritonia_m"
    if "r-osse" in t or "rosse" in t:
        return "r_osse"
    if "os-se" in t or "osse" in t:
        return "os_se"
    if "ath" in t:
        return "ath"
    if "os" in t or "oblate" in t:
        return "oblate_spheroid"
    if "expo" in t or "exponential" in t:
        return "exponential"
    if "tractrix" in t:
        return "tractrix"
    return None


def _infer_mouth_shape(text):
    t = (text or "").lower()
    if "ellipse" in t or "elliptic" in t or "橢圓" in text:
        return "ellipse"
    if "rect" in t or "rectangle" in t or "方形" in text or "矩形" in text:
        return "rect"
    if "round" in t or "circle" in t or "圓形" in text:
        return "round"
    return None


def _parse_frequency_band_hz(freq_band):
    if not freq_band:
        return None, None
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", str(freq_band))
    if not m:
        return None, None
    return float(m.group(1)), float(m.group(2))


def _optimize_waveguide_defaults(inferred):
    low_hz, high_hz = _parse_frequency_band_hz(inferred.get("frequency_band"))
    mouth_w = inferred.get("mouth_width")
    mouth_h = inferred.get("mouth_height")
    mouth_shape = inferred.get("mouth_shape") or "ellipse"
    inferred["mouth_shape"] = mouth_shape

    if mouth_w is None and mouth_h is not None:
        mouth_w = mouth_h
    if mouth_h is None and mouth_w is not None:
        mouth_h = mouth_w

    if low_hz is not None and mouth_w is None:
        # rough mapping: lower crossover needs larger mouth
        target = max(100.0, min(320.0, 280000.0 / max(low_hz, 400.0)))
        mouth_w = target
        mouth_h = target * (0.75 if mouth_shape == "ellipse" else 1.0)

    if inferred.get("waveguide_type") is None:
        if mouth_shape == "rect":
            inferred["waveguide_type"] = "tractrix"
        elif low_hz is not None and low_hz <= 1600:
            inferred["waveguide_type"] = "exponential"
        else:
            inferred["waveguide_type"] = "r_osse"

    if inferred.get("waveguide_type") == "os_se":
        inferred["waveguide_type"] = "oblate_spheroid"
    elif inferred.get("waveguide_type") == "ath":
        inferred["waveguide_type"] = "exponential" if (low_hz and low_hz < 1800) else "oblate_spheroid"
    elif inferred.get("waveguide_type") == "r_osse":
        inferred["waveguide_type"] = "oblate_spheroid"
    elif inferred.get("waveguide_type") == "tritonia_m":
        inferred["waveguide_type"] = "tritonia_m"

    if inferred.get("depth") is None and mouth_w is not None and inferred.get("throat_diameter") is not None:
        inferred["depth"] = max(28.0, min(90.0, (mouth_w - inferred["throat_diameter"]) * 0.42))
    if inferred.get("wall_thickness") is None:
        inferred["wall_thickness"] = 3.2 if low_hz and low_hz < 1800 else 3.0
    if inferred.get("roundover_radius") is None and mouth_w is not None:
        inferred["roundover_radius"] = max(6.0, min(18.0, mouth_w * 0.08))
    if inferred.get("mouth_flange_size") in (None, 0.0):
        inferred["mouth_flange_size"] = 10.0
    if inferred.get("throat_flange_size") in (None, 0.0):
        inferred["throat_flange_size"] = 6.0

    inferred["mouth_width"] = mouth_w
    inferred["mouth_height"] = mouth_h
    throat = inferred.get("throat_diameter")
    if throat is not None:
        min_mouth = throat * 1.25
        if inferred["mouth_width"] is None or inferred["mouth_width"] <= throat:
            inferred["mouth_width"] = max(min_mouth, 120.0)
        if inferred["mouth_height"] is None or inferred["mouth_height"] <= throat:
            ratio = 0.75 if (inferred.get("mouth_shape") or "ellipse") == "ellipse" else 1.0
            inferred["mouth_height"] = max(min_mouth * ratio, 90.0 * ratio)
        min_depth = throat * 0.45
        if inferred.get("depth") is None or inferred.get("depth") < min_depth:
            inferred["depth"] = max(min_depth, 32.0)
    inferred["front_only"] = True
    inferred["segmentized_horn"] = ("segment" in str(inferred.get("source_text", "")).lower())
    inferred["reinforcement_style"] = "radial_ribs"
    inferred["reinforcement_count"] = 6 if mouth_shape in ("round", "ellipse") else 4
    inferred["reinforcement_thickness"] = max(2.2, float(inferred.get("wall_thickness") or 3.0) * 0.85)
    inferred["reinforcement_height"] = max(6.0, float(inferred.get("wall_thickness") or 3.0) * 2.5)
    inferred["reinforcement_start_radius"] = max(10.0, float(inferred.get("throat_diameter") or 25.4) * 0.45)
    inferred["reinforcement_end_radius"] = max(inferred["reinforcement_start_radius"] + 8.0, (float(inferred.get("mouth_width") or 120.0) * 0.38))
    if inferred.get("waveguide_type") == "tritonia_m":
        inferred.setdefault("throat_angle", 10.0)
        inferred.setdefault("term_s_base", 0.7)
        inferred.setdefault("term_s_cos2", 0.2)
        inferred.setdefault("term_n", 3.7)
        inferred.setdefault("term_q", 0.992)
        inferred.setdefault("morph_rate", 3.0)
        inferred.setdefault("morph_corner_radius", 18.0)
        inferred["mouth_shape"] = inferred.get("mouth_shape") or "round"
        inferred["roundover_radius"] = max(float(inferred.get("roundover_radius") or 8.0), 18.0)
    return inferred


def _question_for(key, unit):
    zh = {
        "frequency_band": "請提供目標頻段 (例: 2000-10000 Hz)",
        "waveguide_type": "請選擇波導型式 (tritonia_m/oblate_spheroid/exponential/tractrix)",
        "throat_angle": "請提供喉口張角半角 (deg)",
        "throat_diameter": "請提供喉口直徑 (mm)",
        "mouth_shape": "請提供出口形狀 (round/ellipse/rect)",
        "mouth_width": "請提供波導出口寬度 (mm)",
        "mouth_height": "請提供波導出口高度 (mm)",
        "depth": "請提供波導深度 (mm)",
        "throat_flange_shape": "請提供喉口法蘭形狀 (round/square/ellipse)",
        "throat_flange_size": "請提供喉口法蘭外擴尺寸 (mm)",
        "mouth_flange_shape": "請提供出口法蘭形狀 (round/square/ellipse)",
        "mouth_flange_size": "請提供出口法蘭外擴尺寸 (mm)",
        "wall_thickness": "請提供薄殼厚度 (mm)",
    }
    return zh.get(key, "請提供 {0} ({1})".format(key, unit))


def _make_param(value, rule):
    return {"value": value, "unit": rule["unit"], "required": rule["required"]}


def _build_waveguide_spec_sections(spec, inferred):
    return {
        "part_type": "acoustic_waveguide",
        "design_intent": {
            "application": "acoustic_directivity_control",
            "target_band": inferred.get("frequency_band"),
            "waveguide_type": inferred.get("waveguide_type"),
            "manufacturing": inferred.get("manufacturing_method", "FDM"),
        },
        "geometry": {
            "throat_diameter": inferred.get("throat_diameter"),
            "mouth_width": inferred.get("mouth_width"),
            "mouth_height": inferred.get("mouth_height"),
            "mouth_shape": inferred.get("mouth_shape"),
            "depth": inferred.get("depth"),
            "roundover_radius": inferred.get("roundover_radius"),
            "wall_thickness": inferred.get("wall_thickness"),
            "profile_type": inferred.get("waveguide_type"),
            "throat_angle": inferred.get("throat_angle"),
            "term_s_base": inferred.get("term_s_base"),
            "term_s_cos2": inferred.get("term_s_cos2"),
            "term_n": inferred.get("term_n"),
            "term_q": inferred.get("term_q"),
            "morph_rate": inferred.get("morph_rate"),
            "morph_corner_radius": inferred.get("morph_corner_radius"),
            "throat_flange_shape": inferred.get("throat_flange_shape"),
            "throat_flange_size": inferred.get("throat_flange_size"),
            "mouth_flange_shape": inferred.get("mouth_flange_shape"),
            "mouth_flange_size": inferred.get("mouth_flange_size"),
            "front_only": inferred.get("front_only", True),
            "reinforcement_style": inferred.get("reinforcement_style", "radial_ribs"),
            "reinforcement_count": inferred.get("reinforcement_count", 6),
            "reinforcement_thickness": inferred.get("reinforcement_thickness", 2.5),
            "reinforcement_height": inferred.get("reinforcement_height", 8.0),
            "reinforcement_start_radius": inferred.get("reinforcement_start_radius", 18.0),
            "reinforcement_end_radius": inferred.get("reinforcement_end_radius", 58.0),
        },
        "mounting": {
            "baffle_width": inferred.get("baffle_width"),
            "baffle_height": inferred.get("baffle_height"),
            "baffle_thickness": inferred.get("baffle_thickness"),
            "screw_count": inferred.get("screw_count"),
            "screw_diameter": inferred.get("screw_diameter"),
            "screw_spacing": inferred.get("screw_spacing"),
        },
        "constraints": {
            "min_wall_thickness": inferred.get("min_wall_thickness"),
            "watertight_required": True,
            "avoid_sharp_edges": True,
        },
        "output": {"format": "STL"},
    }


def create_plan(spec, domain="general", research_excerpt=""):
    t = (spec or "").lower()
    plan = {
        "spec": spec,
        "domain": domain,
        "intent": "create_generic_geometry",
        "backend": "sdf",
        "shape": "cylinder",
        "parameters": {},
        "operations": [],
        "missing_required": [],
        "questions": [],
        "status": "draft",
        "research_excerpt": research_excerpt,
    }

    looks_like_target_waveguide = is_target_waveguide_prompt(spec or "")
    if looks_like_target_waveguide:
        tpl = copy.deepcopy(get_acoustic_template("ath_waveguide") or get_acoustic_template("acoustic_waveguide") or {})
        plan["intent"] = "create_ath_waveguide"
        plan["backend"] = "cadquery"
        plan["shape"] = "waveguide"
        plan["cem_mode"] = "target_driven_waveguide"
        plan["operations"] = tpl.get("operations", [])
        plan["operations"] = [
            {"op": "create_baffle"},
            {"op": "create_acoustic_path"},
            {"op": "boolean_subtract"},
            {"op": "add_roundover"},
            {"op": "add_radial_ribs"},
            {"op": "add_screw_holes"},
            {"op": "validate_mesh"},
            {"op": "export_stl"},
        ]

        mm = _extract_mm_values(spec or "")
        hz = _extract_hz_range(spec or "")
        wg_type = _infer_waveguide_type(spec or "")
        throat_mm = _extract_throat_diameter_mm(spec or "")
        mouth_w_mm, mouth_h_mm = _extract_mouth_wh_mm(spec or "")
        depth_mm = _extract_depth_mm(spec or "")
        wall_mm = _extract_wall_mm(spec or "")

        inferred = {
            "source_text": spec or "",
            "frequency_band": hz,
            "waveguide_type": wg_type,
            "throat_diameter": throat_mm if throat_mm is not None else (mm[0] if len(mm) >= 1 else None),
            "mouth_shape": _infer_mouth_shape(spec or ""),
            "mouth_width": mouth_w_mm if mouth_w_mm is not None else (mm[1] if len(mm) >= 2 else None),
            "mouth_height": mouth_h_mm if mouth_h_mm is not None else (mm[2] if len(mm) >= 3 else None),
            "depth": depth_mm if depth_mm is not None else (mm[3] if len(mm) >= 4 else None),
            "wall_thickness": wall_mm if wall_mm is not None else (mm[4] if len(mm) >= 5 else None),
        }
        inferred = _optimize_waveguide_defaults(inferred)

        for k, rule in ATH_WAVEGUIDE_SCHEMA.items():
            if k not in inferred:
                inferred[k] = rule["default"]
            plan["parameters"][k] = _make_param(inferred[k], rule)

        for key in QUESTION_ORDER:
            rule = ATH_WAVEGUIDE_SCHEMA[key]
            val = inferred.get(key, rule["default"])
            if rule["required"] and val is None:
                plan["missing_required"].append(key)
                plan["questions"].append(_question_for(key, rule["unit"]))

        plan["specification"] = _build_waveguide_spec_sections(spec, inferred)
        warnings, checks = check_waveguide_rules(plan["parameters"])
        plan["warnings"] = warnings
        plan["acoustic_checks"] = checks
        candidates, best = optimize_candidates(plan)
        plan["candidates"] = [
            {"candidate_id": c["candidate_id"], "scores": c["scores"], "waveguide_type": c["parameters"]["waveguide_type"]["value"], "depth": c["parameters"]["depth"]["value"]}
            for c in candidates
        ]
        plan["best_candidate_id"] = best.get("candidate_id")
        plan["best_candidate_scores"] = best.get("scores")
        plan["parameters"] = best["parameters"]
        plan["status"] = "ready" if not plan["missing_required"] else "needs_input"
        return plan

    plan["parameters"] = {
        "radius": {"value": 20.0, "unit": "mm", "required": True},
        "height": {"value": 40.0, "unit": "mm", "required": True},
    }
    plan["status"] = "ready"
    return plan


def apply_confirm(plan, sets):
    out = copy.deepcopy(plan)
    params = out.setdefault("parameters", {})
    for item in sets:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        key = k.strip()
        raw = v.strip()
        try:
            value = float(raw)
        except Exception:
            value = raw
        if key not in params:
            params[key] = {"value": value, "unit": "", "required": False}
        else:
            params[key]["value"] = value

    missing = []
    questions = []
    for key in QUESTION_ORDER + [k for k in params.keys() if k not in QUESTION_ORDER]:
        cfg = params.get(key)
        if not cfg:
            continue
        if cfg.get("required") and cfg.get("value") is None:
            missing.append(key)
            questions.append(_question_for(key, cfg.get("unit", "")))
    out["missing_required"] = missing
    out["questions"] = questions
    out["status"] = "ready" if not missing else "needs_input"

    if out.get("shape") == "waveguide":
        inferred = {k: v.get("value") for k, v in params.items()}
        out["specification"] = _build_waveguide_spec_sections(out.get("spec", ""), inferred)
        warnings, checks = check_waveguide_rules(out["parameters"])
        out["warnings"] = warnings
        out["acoustic_checks"] = checks
        candidates, best = optimize_candidates(out)
        out["candidates"] = [
            {"candidate_id": c["candidate_id"], "scores": c["scores"], "waveguide_type": c["parameters"]["waveguide_type"]["value"], "depth": c["parameters"]["depth"]["value"]}
            for c in candidates
        ]
        out["best_candidate_id"] = best.get("candidate_id")
        out["best_candidate_scores"] = best.get("scores")
        out["parameters"] = best["parameters"]
    return out


def load_plan(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_plan(path, plan):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
