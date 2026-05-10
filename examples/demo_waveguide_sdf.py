from __future__ import annotations

from pathlib import Path

from labcem.export.exporter import export_obj, export_report_json, export_stl
from labcem.shapes.waveguide import create_waveguide
from labcem.validation.geometry_validator import GeometryValidator


def main() -> None:
    spec = {
        "type": "waveguide",
        "throat_diameter": 25.0,
        "mouth_width": 180.0,
        "mouth_height": 120.0,
        "depth": 90.0,
        "directivity_h": 90.0,
        "directivity_v": 60.0,
        "bandwidth": [1000, 18000],
        "wall_thickness": 3.0,
        "flange_thickness": 8.0,
        "resolution": 1.0,
        "backend": "python_sdf",
    }

    outputs_dir = Path("outputs")
    stl_path = outputs_dir / "waveguide_demo.stl"
    obj_path = outputs_dir / "waveguide_demo.obj"
    report_path = outputs_dir / "validation_report.json"

    result = create_waveguide(spec)
    mesh = result.get("mesh")

    validator = GeometryValidator()
    report = {
        "required_fields_ok": validator.validate_required_fields(spec),
        "dimension_range_ok": validator.validate_dimension_range(spec),
        "wall_thickness_ok": validator.validate_wall_thickness(spec),
        "mesh_exists_ok": validator.validate_mesh_exists(mesh),
    }

    export_stl(mesh, stl_path)
    export_obj(mesh, obj_path)
    report["export_success_ok"] = validator.validate_export_success(stl_path)
    report["backend"] = result.get("backend")
    report["bbox"] = result.get("bbox")
    report["issues"] = list(validator.issues)
    report["valid"] = all(report[k] for k in [
        "required_fields_ok",
        "dimension_range_ok",
        "wall_thickness_ok",
        "mesh_exists_ok",
        "export_success_ok",
    ])

    export_report_json(report, report_path)

    print("=== Waveguide SDF Demo ===")
    print("spec:", spec)
    print("stl:", stl_path)
    print("obj:", obj_path)
    print("report:", report_path)
    print("validation:", report)


if __name__ == "__main__":
    main()
