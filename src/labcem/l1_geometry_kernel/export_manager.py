import csv
import json
from datetime import datetime
from pathlib import Path

from labcem.l1.exporters import export_geometry
from labcem.l1.mesh_export import export_obj, export_stl_ascii


def _write_csv(path, rows, headers):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_all(output_path, geometry_obj, verts, faces, run_payload=None):
    output_path = Path(output_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_path.parent / (output_path.stem + "_" + ts)
    run_dir.mkdir(parents=True, exist_ok=True)

    out_json = run_dir / "geometry.json"
    out_json = export_geometry(geometry_obj, out_json)

    mesh_stl = run_dir / "model.stl"
    mesh_obj = run_dir / "model.obj"
    mesh_step = run_dir / "model.step"
    mesh_3mf = run_dir / "model.3mf"

    export_stl_ascii(verts, faces, mesh_stl, name="labcem")
    export_obj(verts, faces, mesh_obj)

    # STEP/3MF not implemented yet - intentionally not exporting placeholder geometry files.

    payload = run_payload or {}
    (run_dir / "build_report.json").write_text(json.dumps(payload.get("build_report", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "validation_report.json").write_text(json.dumps(payload.get("validation_report", {}), ensure_ascii=False, indent=2), encoding="utf-8")

    profile_samples = payload.get("profile_samples", [])
    if profile_samples:
        _write_csv(run_dir / "profile_samples.csv", profile_samples, headers=["z", "rx", "ry"])

    params = payload.get("parameter_table", {})
    if params:
        rows = [{"parameter": k, "value": v} for k, v in params.items()]
        _write_csv(run_dir / "parameter_table.csv", rows, headers=["parameter", "value"])

    return out_json, mesh_stl, mesh_obj, run_dir, None, None
