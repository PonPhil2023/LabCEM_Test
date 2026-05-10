import json
import os
import re
import subprocess
from pathlib import Path

from labcem.config import DEFAULT_LABEL9_MODEL_PATH, FALLBACK_LABEL9_MODEL_PATH


class Label9Generator:
    def __init__(self, model_path=DEFAULT_LABEL9_MODEL_PATH):
        model_dir = Path(model_path)
        if not model_dir.exists():
            fallback = Path(FALLBACK_LABEL9_MODEL_PATH)
            if fallback.exists():
                model_dir = fallback
        self.model_path = model_dir
        self.cli_repo = Path(r"D:\Code\Label9_desktop-windows_fix")
        self.cli_js = self.cli_repo / "Electron_app" / "bin" / "labelnine.js"
        self.runtime_dir = Path(r"D:\Code\CEM_Test\Label9_runtime")

    def _extract_json(self, text):
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None


    def _extract_mm_numbers(self, text):
        values = []
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*mm", text, flags=re.IGNORECASE):
            try:
                values.append(float(m.group(1)))
            except Exception:
                continue
        return values

    def _extract_hz_range(self, text):
        s = text or ""
        m = re.search(r"(\d+(?:\.\d+)?)\s*(k)?\s*hz\s*[-~to]{1,3}\s*(\d+(?:\.\d+)?)\s*(k)?\s*hz", s, flags=re.IGNORECASE)
        if m:
            a = float(m.group(1)) * (1000.0 if m.group(2) else 1.0)
            b = float(m.group(3)) * (1000.0 if m.group(4) else 1.0)
            lo, hi = min(a, b), max(a, b)
            return "{0:.0f}-{1:.0f}".format(lo, hi)
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*(k)?\s*hz", s, flags=re.IGNORECASE)
        if m2:
            mul = 1000.0 if m2.group(3) else 1.0
            a = float(m2.group(1)) * mul
            b = float(m2.group(2)) * mul
            lo, hi = min(a, b), max(a, b)
            return "{0:.0f}-{1:.0f}".format(lo, hi)
        return None

    def _extract_coverage_deg(self, text):
        s = (text or "").lower()
        m = re.search(r"[\+\-]?\s*(\d+(?:\.\d+)?)\s*度", s)
        if m:
            try:
                v = float(m.group(1))
                return max(20.0, min(120.0, abs(v) * 2.0))
            except Exception:
                return None
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*deg", s)
        if m2:
            try:
                return max(20.0, min(120.0, float(m2.group(1))))
            except Exception:
                return None
        return None

    def _infer_instruction_from_text(self, text):
        t = (text or "").lower()
        if not t.strip():
            return None

        # Hex bolt intent
        if ("m4" in t) or ("螺絲" in text) or ("screw" in t) or ("bolt" in t) or ("六角" in text) or ("hex" in t):
            shaft_radius = 2.0
            head_radius = 4.0
            if "m3" in t:
                shaft_radius, head_radius = 1.5, 3.0
            elif "m5" in t:
                shaft_radius, head_radius = 2.5, 4.5
            elif "m6" in t:
                shaft_radius, head_radius = 3.0, 5.5
            return {
                "shape": "hex_bolt",
                "shaft_radius": shaft_radius,
                "shaft_length": 26.0,
                "head_radius": head_radius,
                "head_height": 3.0,
            }

        if ("cylinder" in t) or ("圓柱" in text):
            return {"shape": "cylinder", "radius": 12.0, "height": 36.0, "backend": "cadquery"}

        if ("waveguide" in t) or ("horn" in t) or ("號角" in text) or ("波導" in text):
            dims = self._extract_mm_numbers(text or "")
            throat_d = dims[0] if len(dims) >= 1 else 25.4
            freq_band = self._extract_hz_range(text or "") or "2000-16000"
            cov = self._extract_coverage_deg(text or "")
            is_tritonia = ("tritonia" in t) or ("ath" in t)
            return {
                "intent": "create_acoustic_waveguide",
                "backend": "cadquery",
                "shape": "waveguide",
                "waveguide_type": "tritonia_m" if is_tritonia else "oblate_spheroid",
                "throat_radius": throat_d * 0.5,
                "throat_diameter": throat_d,
                "mouth_radius": 60.0,
                "depth": 35.0,
                "wall_thickness": 3.0,
                "frequency_band": freq_band,
                "horizontal_coverage_deg": cov if cov is not None else 90.0,
                "vertical_coverage_deg": (cov * 0.67) if cov is not None else 60.0,
                "throat_angle": 10.0,
                "term_s_base": 0.7,
                "term_s_cos2": 0.2,
                "term_n": 3.7,
                "term_q": 0.992,
                "morph_rate": 3.0,
                "morph_corner_radius": 18.0,
                "operations": [{"op": "shell", "thickness": 3.0}],
            }

        if ("sphere" in t) or ("球" in text):
            # Map sphere request to torus-like fallback not ideal; use compact torus approximation if unsupported.
            return {"shape": "sphere", "radius": 10.0}

        if ("torus" in t) or ("ring" in t) or ("donut" in t) or ("甜甜圈" in text):
            return {"shape": "torus", "major_radius": 24.0, "minor_radius": 7.0, "backend": "sdf"}
        return None

    def _cli_status(self, available=False, ok=False, exit_code=None, reason="", mode="fallback"):
        return {
            "available": bool(available),
            "ok": bool(ok),
            "exit_code": exit_code,
            "reason": reason,
            "mode": mode,
        }

    def _generate_with_label9_cli(self, prompt):
        if not self.cli_js.exists():
            return None, self._cli_status(available=False, reason="labelnine.js not found"), ""

        synth_prompt = (
            "請先思考並視需要搜尋，再回答。"
            "最後一行請輸出一個 JSON 物件。"
            "請至少包含：intent, backend, shape。"
            "可用 shape: torus, cylinder, hex_bolt, sphere, waveguide, horn。"
            "若可行請附上 operations 陣列。"
            "使用者需求：" + prompt
        )

        env = os.environ.copy()
        env["LABELNINE_APP_DATA_DIR"] = str(self.runtime_dir)
        modes = [
            ("ask", ["node", str(self.cli_js), "ask", "--think", "--hide-think", synth_prompt], 60),
            ("chat", ["node", str(self.cli_js), "chat", "--think", "--hide-think", synth_prompt], 75),
        ]

        last_status = self._cli_status(available=True, ok=False, reason="unknown", mode="fallback")
        last_raw = ""

        for mode_name, cmd, timeout_sec in modes:
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.cli_repo),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                )
            except subprocess.TimeoutExpired:
                last_status = self._cli_status(available=True, ok=False, reason="timeout:{0}".format(mode_name), mode="fallback")
                last_raw = "timeout on mode={0}".format(mode_name)
                continue
            except OSError as exc:
                last_status = self._cli_status(available=True, ok=False, reason=str(exc), mode="fallback")
                last_raw = str(exc)
                continue

            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            last_raw = out
            payload = self._extract_json(out)
            if payload:
                payload["source"] = "label9_cli"
                return payload, self._cli_status(available=True, ok=True, exit_code=proc.returncode, reason="ok:{0}".format(mode_name), mode="label9_cli"), out

            inferred = self._infer_instruction_from_text(out)
            if inferred:
                inferred["source"] = "label9_cli_text"
                return inferred, self._cli_status(available=True, ok=True, exit_code=proc.returncode, reason="parsed_text:{0}".format(mode_name), mode="label9_cli_text"), out

            last_status = self._cli_status(available=True, ok=False, exit_code=proc.returncode, reason="no_json:{0}".format(mode_name), mode="fallback")

        return None, last_status, last_raw

    def _fallback_instruction(self, prompt):
        text = (prompt or "").lower()
        digest = abs(hash(prompt)) % 100000
        dims_mm = self._extract_mm_numbers(prompt or "")

        if ("nose cone" in text) or ("nosecone" in text) or ("nose" in text and "cone" in text) or ("rocket" in text and "cone" in text):
            depth = dims_mm[0] if len(dims_mm) >= 1 else 80.0
            base_diameter = dims_mm[1] if len(dims_mm) >= 2 else 40.0
            mouth_radius = max(4.0, base_diameter / 2.0)
            return {
                "intent": "create_conical_body",
                "backend": "sdf",
                "shape": "horn",
                "throat_radius": max(1.5, mouth_radius * 0.12),
                "mouth_radius": mouth_radius,
                "depth": depth,
                "operations": [],
                "model_path": str(self.model_path),
                "prompt_digest": digest,
                "source": "fallback",
            }

        if ("m4" in text) or ("螺絲" in text) or ("screw" in text) or ("bolt" in text) or ("hex" in text) or ("六角" in text):
            shaft_radius = 2.0
            shaft_length = 26.0
            head_radius = 4.0
            head_height = 3.0
            if "m3" in text:
                shaft_radius = 1.5
                head_radius = 3.0
            elif "m5" in text:
                shaft_radius = 2.5
                head_radius = 4.5
            elif "m6" in text:
                shaft_radius = 3.0
                head_radius = 5.5

            if "long" in text or "長" in text:
                shaft_length *= 1.4
            if "short" in text or "短" in text:
                shaft_length *= 0.7

            return {
                "shape": "hex_bolt",
                "shaft_radius": shaft_radius,
                "shaft_length": shaft_length,
                "head_radius": head_radius,
                "head_height": head_height,
                "model_path": str(self.model_path),
                "prompt_digest": digest,
                "source": "fallback",
                "backend": "sdf",
            }

        shape = "torus"
        backend = "sdf"
        if "waveguide" in text or "horn" in text or "號角" in prompt or "波導" in prompt:
            return {
                "intent": "create_acoustic_waveguide",
                "backend": "cadquery",
                "shape": "waveguide",
                "throat_radius": 12.7,
                "mouth_radius": 60.0,
                "depth": 35.0,
                "wall_thickness": 3.0,
                "operations": [{"op": "shell", "thickness": 3.0}],
                "model_path": str(self.model_path),
                "prompt_digest": digest,
                "source": "fallback",
            }
        if "cylinder" in text or "圓柱" in text:
            shape = "cylinder"
            backend = "cadquery"

        size_scale = 1.0
        if "large" in text or "bigger" in text or "大" in text:
            size_scale = 1.35
        elif "small" in text or "smaller" in text or "小" in text:
            size_scale = 0.75

        thickness_scale = 1.0
        if "thick" in text or "厚" in text:
            thickness_scale = 1.3
        elif "thin" in text or "薄" in text:
            thickness_scale = 0.75

        if shape == "cylinder":
            radius = (10.0 + float(digest % 10)) * size_scale
            height = (24.0 + float(digest % 30)) * size_scale
            return {
                "shape": "cylinder",
                "radius": radius,
                "height": height,
                "model_path": str(self.model_path),
                "prompt_digest": digest,
                "source": "fallback",
                "backend": backend,
            }

        major_radius = (20.0 + float(digest % 10)) * size_scale
        minor_radius = (6.0 + float(digest % 4)) * thickness_scale
        return {
            "shape": "torus",
            "major_radius": major_radius,
            "minor_radius": minor_radius,
            "model_path": str(self.model_path),
            "prompt_digest": digest,
            "source": "fallback",
            "backend": backend,
        }

    def _normalize_instruction(self, ins):
        def _default_if_none(key, value):
            if ins.get(key) is None:
                ins[key] = value

        shape = ins.get("shape", "torus")
        if shape not in ("torus", "cylinder", "hex_bolt", "sphere", "waveguide", "horn"):
            shape = "torus"

        ins["shape"] = shape
        if shape == "cylinder":
            _default_if_none("radius", 12.0)
            _default_if_none("height", 36.0)
            ins.setdefault("radius", 12.0)
            ins.setdefault("height", 36.0)
        elif shape == "hex_bolt":
            _default_if_none("shaft_radius", 2.0)
            _default_if_none("shaft_length", 26.0)
            _default_if_none("head_radius", 4.0)
            _default_if_none("head_height", 3.0)
            ins.setdefault("shaft_radius", 2.0)
            ins.setdefault("shaft_length", 26.0)
            ins.setdefault("head_radius", 4.0)
            ins.setdefault("head_height", 3.0)
        elif shape == "sphere":
            _default_if_none("radius", 10.0)
            ins.setdefault("radius", 10.0)
        elif shape in ("waveguide", "horn"):
            _default_if_none("throat_radius", 12.7)
            _default_if_none("mouth_radius", 60.0)
            _default_if_none("depth", 35.0)
            _default_if_none("wall_thickness", 3.0)
            ins.setdefault("throat_radius", 12.7)
            ins.setdefault("mouth_radius", 60.0)
            ins.setdefault("depth", 35.0)
            ins.setdefault("wall_thickness", 3.0)
        else:
            _default_if_none("major_radius", 24.0)
            _default_if_none("minor_radius", 7.0)
            ins.setdefault("major_radius", 24.0)
            ins.setdefault("minor_radius", 7.0)
        ins.setdefault("backend", "sdf")
        ins.setdefault("operations", [])
        return ins

    def generate_instruction(self, prompt):
        digest = abs(hash(prompt)) % 100000
        cli_instruction, cli_status, cli_raw_output = self._generate_with_label9_cli(prompt)

        if cli_instruction:
            out = self._normalize_instruction(cli_instruction)
            out.setdefault("model_path", str(self.model_path))
            out.setdefault("prompt_digest", digest)
            out["cli_status"] = cli_status
            out["cli_raw_output"] = cli_raw_output
            return out

        out = self._normalize_instruction(self._fallback_instruction(prompt))
        out["cli_status"] = cli_status
        out["cli_raw_output"] = cli_raw_output
        return out

    def summarize(self, run_result):
        steps = run_result.get("pipeline_steps", [])
        tokens = []
        for item in steps:
            tokens.append("{0}:{1}".format(item.get("layer"), item.get("status")))
        return "Label9 Summary | model={0} | voxels={1} | lattice={2} | source={3} | steps={4}".format(
            self.model_path,
            run_result.get("voxel_count", 0),
            run_result.get("lattice_enabled", False),
            run_result.get("source", "unknown"),
            ", ".join(tokens),
        )

    def to_json(self):
        return json.dumps({"model_path": str(self.model_path)}, ensure_ascii=False)

