from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _to_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv_if_available(root: Path | None = None) -> None:
    env_path = (root or Path.cwd()) / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        # Fallback parser: keep behavior safe by not overriding existing env vars.
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            k = key.strip().lstrip("\ufeff")
            if not k or k in os.environ:
                continue
            v = value.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            os.environ[k] = v
        return

    load_dotenv(dotenv_path=env_path, override=False)


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-5.5-thinking"
    api_key: str = ""
    base_url: str = ""
    enabled: bool = False
    timeout_seconds: int = 60
    retry_count: int = 2
    labelnine_shortcut: str = r"C:\Users\user\Desktop\CEM_Test Label9.lnk"
    labelnine_cli_repo: str = r"D:\Code\Label9_desktop-windows_fix"
    labelnine_runtime_dir: str = r"C:\Users\user\AppData\Roaming\Label9\runtime"
    labelnine_runtime_port: str = "18789"

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "LLMConfig":
        _load_dotenv_if_available(project_root)
        provider = os.getenv("LABCEM_LLM_PROVIDER", "openai").strip() or "openai"
        model = os.getenv("LABCEM_LLM_MODEL", "gpt-5.5-thinking").strip() or "gpt-5.5-thinking"
        api_key = os.getenv("LABCEM_LLM_API_KEY", "").strip()
        base_url = os.getenv("LABCEM_LLM_BASE_URL", "").strip()
        enabled_env = _to_bool(os.getenv("LABCEM_LLM_ENABLED", "false"), default=False)

        if provider.lower() == "labelnine":
            provider = "labelnine_cli"

        labelnine_shortcut = os.getenv("LABCEM_LABELNINE_SHORTCUT", r"C:\Users\user\Desktop\CEM_Test Label9.lnk").strip()
        labelnine_cli_repo = os.getenv("LABCEM_LABELNINE_CLI_REPO", r"D:\Code\Label9_desktop-windows_fix").strip()
        labelnine_runtime_dir = os.getenv("LABCEM_LABELNINE_RUNTIME_DIR", r"C:\Users\user\AppData\Roaming\Label9\runtime").strip()
        labelnine_runtime_port = os.getenv("LABCEM_LABELNINE_RUNTIME_PORT", "18789").strip() or "18789"

        if provider == "labelnine_cli":
            enabled = bool(enabled_env)
        else:
            enabled = bool(enabled_env and api_key)

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            enabled=enabled,
            labelnine_shortcut=labelnine_shortcut,
            labelnine_cli_repo=labelnine_cli_repo,
            labelnine_runtime_dir=labelnine_runtime_dir,
            labelnine_runtime_port=labelnine_runtime_port,
        )

    def status_dict(self) -> dict:
        return {
            "enabled": bool(self.enabled),
            "provider": self.provider,
            "model": self.model,
            "base_url_set": bool(self.base_url),
            "api_key_found": bool(self.api_key),
            "labelnine_shortcut_exists": Path(self.labelnine_shortcut).exists(),
            "labelnine_runtime_port": self.labelnine_runtime_port,
            "message": "LLM enabled" if self.enabled else "LLM is not enabled. Set LABCEM_LLM_ENABLED=true and provide LABCEM_LLM_API_KEY.",
        }

