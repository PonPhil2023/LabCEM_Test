from __future__ import annotations

import re
from typing import List


class FormulaExtractor:
    TOKENS = ["=", "sin", "cos", "tan", "log", "exp", "sqrt", "radius", "area", "angle"]

    def extract(self, text: str) -> List[str]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        out = []
        for ln in lines:
            low = ln.lower()
            if any(tok in low for tok in self.TOKENS) and re.search(r"[0-9a-zA-Z_\)\]]\s*=\s*", ln):
                out.append(ln)
            elif any(tok in low for tok in self.TOKENS) and any(ch.isdigit() for ch in ln):
                out.append(ln)
        return out[:200]
