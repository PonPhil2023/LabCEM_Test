from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

from .llm_config import LLMConfig


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config

    def is_available(self) -> bool:
        if not self.config.enabled:
            return False
        if self.config.provider == "labelnine_cli":
            return True
        return bool(self.config.api_key)

    def complete_json(self, system_prompt: str, user_prompt: str, schema: dict | None = None) -> dict:
        if not self.is_available():
            return {"ok": False, "message": "LLM unavailable", "errors": ["LLM disabled or API key missing"]}

        raw = self.complete_text(system_prompt, user_prompt)
        if isinstance(raw, dict) and raw.get("ok") is False:
            return raw
        try:
            data = json.loads(raw)
            if schema is not None:
                data.setdefault("_expected_schema", schema.get("title", "schema"))
            if "ok" not in data:
                data["ok"] = True
            return data
        except Exception as exc:
            return {"ok": False, "parse_error": str(exc), "raw_response": raw}

    def complete_text(self, system_prompt: str, user_prompt: str) -> str | Dict[str, Any]:
        if not self.is_available():
            return {"ok": False, "message": "LLM unavailable", "errors": ["LLM disabled or API key missing"]}

        if self.config.provider == "labelnine_cli":
            return self._complete_with_labelnine_cli(system_prompt, user_prompt)

        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            return {"ok": False, "message": "openai package is required. Please run: pip install openai", "errors": ["missing_openai_package"]}

        kwargs: Dict[str, Any] = {"api_key": self.config.api_key, "timeout": self.config.timeout_seconds}
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url

        client = OpenAI(**kwargs)
        errs = []
        for i in range(self.config.retry_count + 1):
            try:
                resp = client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as exc:
                errs.append(str(exc))
                if i < self.config.retry_count:
                    time.sleep(1.0)
        return {"ok": False, "message": "LLM request failed", "errors": errs}

    def _complete_with_labelnine_cli(self, system_prompt: str, user_prompt: str) -> str | Dict[str, Any]:
        cli_repo = Path(self.config.labelnine_cli_repo)
        cli_js = cli_repo / "Electron_app" / "bin" / "labelnine.js"
        if not cli_js.exists():
            return {"ok": False, "message": f"Labelnine CLI not found: {cli_js}", "errors": ["labelnine_cli_missing"]}

        synth_prompt = (
            "請只輸出合法 JSON，不要包含 markdown code block。\n"
            + "System:\n"
            + system_prompt
            + "\n\nUser:\n"
            + user_prompt
        )

        env = os.environ.copy()
        env["LABELNINE_APP_DATA_DIR"] = self.config.labelnine_runtime_dir
        env["CODEX_RUNTIME_PORT"] = str(self.config.labelnine_runtime_port)

        errs = []
        for i in range(self.config.retry_count + 1):
            try:
                proc = subprocess.run(
                    ["node", str(cli_js), "ask", "--think", "--hide-think", synth_prompt],
                    cwd=str(cli_repo),
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                    env=env,
                )
                out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
                if proc.returncode == 0 and out:
                    return out
                errs.append(f"exit={proc.returncode}")
            except Exception as exc:
                errs.append(str(exc))
            if i < self.config.retry_count:
                time.sleep(1.0)
        return {"ok": False, "message": "Labelnine CLI request failed", "errors": errs}

