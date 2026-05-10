from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DocumentImporter:
    SUPPORTED = {".txt", ".md", ".json", ".pdf", ".docx"}
    FALLBACK_ENCODINGS = ["utf-8", "cp950", "big5", "latin-1"]

    def __init__(self, kernels_root: Path | None = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[1] / "kernels"

    def import_sources(self, kernel_id: str, paths: List[str], source_id: str | None = None) -> Dict:
        src_paths = [Path(p) for p in paths]
        source_id = source_id or self._derive_source_id(src_paths)
        out_dir = self.kernels_root / kernel_id / "knowledge" / "sources"
        out_dir.mkdir(parents=True, exist_ok=True)

        entries = []
        chunks = []
        errors = []
        for p in src_paths:
            rec = {"path": str(p), "type": p.suffix.lower().lstrip("."), "status": "ok", "chars": 0}
            try:
                text = self._read_file(p)
                rec["chars"] = len(text)
                chunks.append(f"\n\n# SOURCE: {p.name}\n{text}")
            except Exception as exc:
                rec["status"] = "error"
                errors.append(f"{p}: {exc}")
            entries.append(rec)

        payload = {
            "source_id": source_id,
            "kernel_id": kernel_id,
            "source_files": entries,
            "combined_text": "\n".join(chunks).strip(),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "errors": errors,
        }
        output_path = out_dir / f"{source_id}.clean_text.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "ok": len(errors) == 0,
            "message": "Documents imported" if not errors else "Documents imported with warnings",
            "source_id": source_id,
            "output": str(output_path),
            "errors": errors,
        }

    def _read_file(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            raise ValueError("file not found")
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED:
            raise ValueError(f"unsupported file type: {ext}")
        if ext in {".txt", ".md"}:
            return self._read_text(path)
        if ext == ".json":
            return self._read_json_summary(path)
        if ext == ".pdf":
            return self._read_pdf(path)
        if ext == ".docx":
            return self._read_docx(path)
        return self._read_text(path)

    def _read_text(self, path: Path) -> str:
        last_err = None
        for enc in self.FALLBACK_ENCODINGS:
            try:
                return path.read_text(encoding=enc)
            except Exception as exc:  # pragma: no cover - depends on file encoding
                last_err = exc
        raise ValueError(f"unable to decode text file: {last_err}")

    def _read_json_summary(self, path: Path) -> str:
        raw = self._read_text(path)
        data = json.loads(raw)
        if isinstance(data, dict):
            keys = ", ".join(list(data.keys())[:50])
            return f"JSON object with keys: {keys}\n\n{json.dumps(data, ensure_ascii=False, indent=2)[:20000]}"
        if isinstance(data, list):
            return f"JSON list length={len(data)}\n\n{json.dumps(data[:50], ensure_ascii=False, indent=2)}"
        return str(data)

    def _read_pdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise RuntimeError("PDF import requires pypdf. Please run: pip install pypdf") from exc

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    def _read_docx(self, path: Path) -> str:
        try:
            import docx
        except Exception as exc:
            raise RuntimeError("DOCX import requires python-docx. Please run: pip install python-docx") from exc

        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text).strip()

    def _derive_source_id(self, paths: List[Path]) -> str:
        if len(paths) == 1:
            return paths[0].stem.replace(" ", "_")
        base = "_".join(p.stem for p in paths[:3]).replace(" ", "_")
        return f"multi_{base}"[:80]
