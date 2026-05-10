from pathlib import Path

from labcem.acoustic.solver import DesignSolver
from labcem.core.spec import DesignSpec
from labcem.export.exporter import ExportManager
from labcem.shapes.waveguide import create_waveguide
from labcem.validation.validator import GeometryValidator


def main() -> None:
    spec = DesignSpec(
        type="waveguide",
        throat_diameter=25.0,
        mouth_width=180.0,
        mouth_height=120.0,
        depth=90.0,
        directivity_h=90.0,
        directivity_v=60.0,
        bandwidth=(1000.0, 18000.0),
        wall_thickness=3.0,
        flange_thickness=8.0,
        resolution=2.0,
    )

    solver = DesignSolver()
    spec = solver.solve(spec)

    model = create_waveguide(spec, backend="python_sdf")

    validator = GeometryValidator(min_wall_thickness_mm=2.0)
    report = validator.validate(model, spec)

    out_dir = Path("outputs")
    exporter = ExportManager()
    stl_path = exporter.export_stl(model, str(out_dir / "waveguide_demo.stl"))
    report_path = exporter.export_report_json(report, str(out_dir / "waveguide_report.json"))

    print("LabCEM MVP completed.")
    print(f"STL: {stl_path.resolve()}")
    print(f"Report: {report_path.resolve()}")
    print(f"Validation OK: {report['ok']}")


if __name__ == "__main__":
    main()
