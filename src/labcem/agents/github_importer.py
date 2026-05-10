from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class GitHubImporter:
    MAX_FILE_BYTES = 300 * 1024
    SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", "dist", "build", "outputs"}
    CANDIDATE_NAMES = {"pyproject.toml", "requirements.txt"}
    CANDIDATE_DIRS = {"docs", "src", "examples", "tests"}

    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"

    def import_repo(self, kernel_id: str, repo_path: str, source_id: str | None = None) -> Dict:
        root = Path(repo_path)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"invalid repo/folder path: {repo_path}")

        source_id = source_id or f"repo_{root.name.replace(' ', '_')}"
        out_dir = self.kernels_root / kernel_id / "knowledge" / "sources"
        out_dir.mkdir(parents=True, exist_ok=True)

        detected_files = self._scan_candidates(root)
        read_files: List[str] = []
        chunks: List[str] = []
        errors: List[str] = []

        for path in detected_files:
            try:
                if path.stat().st_size > self.MAX_FILE_BYTES:
                    errors.append(f"skip large file: {path}")
                    continue
                text = self._read_text(path)
                read_files.append(str(path))
                chunks.append(f"\n\n# FILE: {path.relative_to(root)}\n{text}")
            except Exception as exc:
                errors.append(f"{path}: {exc}")

        combined = "\n".join(chunks).strip()
        payload = {
            "source_id": source_id,
            "kernel_id": kernel_id,
            "repo_path": str(root),
            "detected_files": [str(p) for p in detected_files],
            "read_files": read_files,
            "combined_text": combined,
            "possible_components": self._detect_possible_components(combined),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "errors": errors,
        }

        output_path = out_dir / f"{source_id}.repo_summary.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": len(read_files) > 0,
            "message": "Repo imported" if not errors else "Repo imported with warnings",
            "source_id": source_id,
            "output": str(output_path),
            "errors": errors,
        }

    def _scan_candidates(self, root: Path) -> List[Path]:
        found: List[Path] = []

        for child in root.iterdir():
            if child.name in self.SKIP_DIRS:
                continue
            if child.is_file() and (child.name.lower().startswith("readme") or child.name in self.CANDIDATE_NAMES):
                found.append(child)

        for d in self.CANDIDATE_DIRS:
            p = root / d
            if p.exists() and p.is_dir():
                for f in p.rglob("*"):
                    if not f.is_file():
                        continue
                    if any(part in self.SKIP_DIRS for part in f.parts):
                        continue
                    if f.suffix.lower() in {".md", ".txt", ".py", ".json", ".toml", ".yaml", ".yml"}:
                        found.append(f)

        # de-duplicate while keeping order
        out: List[Path] = []
        seen = set()
        for p in found:
            k = str(p.resolve())
            if k not in seen:
                seen.add(k)
                out.append(p)
        return out

    def _read_text(self, path: Path) -> str:
        for enc in ["utf-8", "cp950", "big5", "latin-1"]:
            try:
                return path.read_text(encoding=enc)
            except Exception:
                pass
        return ""

    def _detect_possible_components(self, text: str) -> List[str]:
        s = text.lower()
        possible = []
        for c in ["waveguide", "horn", "diffuser", "cavity", "port", "midsole", "bracket"]:
            if c in s:
                possible.append(c)
        return possible
