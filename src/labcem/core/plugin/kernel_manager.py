from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Dict, Optional


class KernelManager:
    def __init__(self, kernels_root: Optional[Path] = None):
        self.kernels_root = kernels_root or Path(__file__).resolve().parents[2] / "kernels"
        self._manifests: Dict[str, Dict] = {}
        self._instances: Dict[str, object] = {}
        self.scan()

    def scan(self) -> Dict[str, Dict]:
        self._manifests = {}
        if not self.kernels_root.exists():
            return self._manifests
        for mf in self.kernels_root.glob("*/kernel_manifest.json"):
            data = json.loads(mf.read_text(encoding="utf-8-sig"))
            kid = data.get("kernel_id")
            if kid:
                self._manifests[kid] = data
        return self._manifests

    def list_kernels(self):
        return list(self._manifests.keys())

    def get_manifest(self, kernel_id: str) -> Dict:
        if kernel_id not in self._manifests:
            raise ValueError(f"Kernel manifest not found: {kernel_id}")
        return self._manifests[kernel_id]

    def load_kernel(self, kernel_id: str):
        if kernel_id in self._instances:
            return self._instances[kernel_id]
        mf = self.get_manifest(kernel_id)
        entry = mf.get("entry_point", "")
        if ":" not in entry:
            raise ValueError(f"Invalid entry point for kernel {kernel_id}: {entry}")
        mod_name, cls_name = entry.split(":", 1)
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
        inst = cls()
        self._instances[kernel_id] = inst
        return inst

    def get_active_kernel(self, kernel_id: str):
        return self.load_kernel(kernel_id)
