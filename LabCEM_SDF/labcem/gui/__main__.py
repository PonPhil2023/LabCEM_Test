from __future__ import annotations

import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from labcem.core.spec import DesignSpec
from labcem.export.exporter import ExportManager
from labcem.shapes.waveguide import create_waveguide
from labcem.validation.validator import GeometryValidator


class LabCEMGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("LabCEM SDF GUI")
        self.root.geometry("560x520")
        self.output_dir = Path.cwd() / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._build_ui()

    def _build_ui(self) -> None:
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Waveguide MVP Parameters", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.entries = {}
        fields = [
            ("throat_diameter", "25.0"),
            ("mouth_width", "180.0"),
            ("mouth_height", "120.0"),
            ("depth", "90.0"),
            ("directivity_h", "90.0"),
            ("directivity_v", "60.0"),
            ("wall_thickness", "3.0"),
            ("flange_thickness", "8.0"),
            ("resolution", "2.0"),
        ]

        for idx, (name, default) in enumerate(fields, start=1):
            ttk.Label(frm, text=name).grid(row=idx, column=0, sticky="w", pady=4)
            ent = ttk.Entry(frm, width=24)
            ent.insert(0, default)
            ent.grid(row=idx, column=1, sticky="ew", pady=4)
            self.entries[name] = ent

        frm.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Button(btn_row, text="Generate STL + Report", command=self.on_generate).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Open Outputs Folder", command=self.on_open_outputs).pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frm, textvariable=self.status_var, foreground="#1f5aa6").grid(row=len(fields) + 2, column=0, columnspan=2, sticky="w", pady=(4, 8))

        self.log = tk.Text(frm, height=12, wrap="word")
        self.log.grid(row=len(fields) + 3, column=0, columnspan=2, sticky="nsew")
        frm.rowconfigure(len(fields) + 3, weight=1)

    def _read_float(self, key: str) -> float:
        return float(self.entries[key].get().strip())

    def on_generate(self) -> None:
        try:
            spec = DesignSpec(
                type="waveguide",
                throat_diameter=self._read_float("throat_diameter"),
                mouth_width=self._read_float("mouth_width"),
                mouth_height=self._read_float("mouth_height"),
                depth=self._read_float("depth"),
                directivity_h=self._read_float("directivity_h"),
                directivity_v=self._read_float("directivity_v"),
                bandwidth=(1000.0, 18000.0),
                wall_thickness=self._read_float("wall_thickness"),
                flange_thickness=self._read_float("flange_thickness"),
                resolution=self._read_float("resolution"),
            )

            model = create_waveguide(spec, backend="python_sdf")
            validator = GeometryValidator(min_wall_thickness_mm=2.0)
            report = validator.validate(model, spec)

            exporter = ExportManager()
            stl_path = exporter.export_stl(model, str(self.output_dir / "waveguide_demo.stl"))
            report_path = exporter.export_report_json(report, str(self.output_dir / "waveguide_report.json"))

            self.status_var.set("Generated successfully")
            self._append_log(f"STL: {stl_path}")
            self._append_log(f"Report: {report_path}")
            self._append_log(f"Validation OK: {report['ok']}")
            self._append_log(json.dumps(report["mesh_stats"], ensure_ascii=False))
            messagebox.showinfo("LabCEM", "Generation completed.")
        except Exception as exc:
            self.status_var.set("Failed")
            self._append_log(f"Error: {exc}")
            messagebox.showerror("LabCEM Error", str(exc))

    def on_open_outputs(self) -> None:
        path = str(self.output_dir.resolve())
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False)

    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)


def main() -> None:
    root = tk.Tk()
    app = LabCEMGuiApp(root)
    app._append_log("LabCEM GUI ready.")
    root.mainloop()


if __name__ == "__main__":
    main()
