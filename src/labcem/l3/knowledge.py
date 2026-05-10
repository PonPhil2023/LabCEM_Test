import json
import re
import zipfile
from pathlib import Path


class KnowledgeBase:
    def __init__(self, domain: str, root):
        self.domain = domain
        self.root = Path(root)
        self.data = self._load()

    def _load(self) -> dict:
        p = self.root / "{0}.json".format(self.domain)
        if not p.exists():
            raise FileNotFoundError("Domain knowledge file not found: {0}".format(p))
        return json.loads(p.read_text(encoding="utf-8"))

    @property
    def constraints(self) -> dict:
        return self.data.get("constraints", {})

    @property
    def excerpt(self) -> str:
        return self.data.get("description", "")


def _extract_pdf_text(path):
    try:
        from pypdf import PdfReader
    except Exception:
        return "[pdf parser unavailable: install pypdf]"
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages[:8]:
        chunks.append((page.extract_text() or "").strip())
    return "\n".join([c for c in chunks if c])


def _extract_docx_text(path):
    with zipfile.ZipFile(str(path), "r") as zf:
        if "word/document.xml" not in zf.namelist():
            return ""
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_attachment_paths(attachment_input):
    if not attachment_input:
        return []
    if isinstance(attachment_input, (list, tuple)):
        items = attachment_input
    else:
        raw = str(attachment_input)
        items = re.split(r"[\n;,]+", raw)
    out = []
    for item in items:
        s = str(item).strip()
        if s:
            out.append(s)
    return out


def load_attachments_excerpt(attachment_input, max_chars=3000):
    paths = _parse_attachment_paths(attachment_input)
    if not paths:
        return ""

    chunks = []
    per_file_chars = max(600, int(max_chars / max(len(paths), 1)))
    for fp in paths[:10]:
        p = Path(fp)
        if not p.exists():
            chunks.append("[attachment missing: {0}]".format(p))
            continue

        ext = p.suffix.lower()
        try:
            if ext == ".pdf":
                content = _extract_pdf_text(p)
            elif ext == ".docx":
                content = _extract_docx_text(p)
            elif ext in (".txt", ".md", ".json"):
                content = p.read_text(encoding="utf-8", errors="ignore")
            else:
                content = "[unsupported attachment type: {0}]".format(ext)
        except Exception as exc:
            content = "[attachment parse failed: {0}]".format(exc)

        content = (content or "").strip()
        if not content:
            content = "[attachment parsed but empty]"
        chunks.append("[file] {0}\n{1}".format(str(p), content[:per_file_chars]))

    return "\n\n".join(chunks)[:max_chars]


def load_attachment_excerpt(file_path, max_chars=2000):
    # Backward-compatible wrapper.
    return load_attachments_excerpt(file_path, max_chars=max_chars)
