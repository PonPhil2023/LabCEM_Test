# LabCEM_SDF

LabCEM_SDF is an AI + Computational Engineering Model (CEM) prototype for acoustic geometry generation.

## Purpose

- Build waveguide/horn/cavity/port acoustic geometry via structured APIs.
- Avoid direct free-form STL generation from AI.
- Use SDF-style modeling as the MVP and keep backend adapters for future PicoGK/OpenVDB migration.

## Relationship to LEAP71 / PicoGK / ShapeKernel

- **LabCEM MVP (this repo):** Python-based SDF prototype for fast iteration.
- **LEAP71/PicoGK:** target production-grade geometry kernel in Stage-3.
- **LEAP71_ShapeKernel:** architectural reference for future `AcousticShapeKernel` function design.

## Supported Acoustic Geometry (MVP)

- Waveguide (implemented)
- Horn (builder skeleton)
- Cavity (builder skeleton)
- Port (builder skeleton)

## Install (Windows PowerShell)

```powershell
cd D:\Code\CEM_Test\LabCEM_SDF
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Run Example

```powershell
python main.py
```

Outputs:

- `outputs/waveguide_demo.stl`
- `outputs/waveguide_report.json`

## Project Structure

- `main.py`: MVP entry point.
- `labcem/core/spec.py`: `DesignSpec`, `AcousticShape`.
- `labcem/core/backends.py`: `SDFBackend` interface and backend adapters.
- `labcem/shapes/waveguide.py`: high-level waveguide API.
- `labcem/shapes/builders.py`: builder classes.
- `labcem/validation/validator.py`: geometry validation report.
- `labcem/export/exporter.py`: STL/3MF/VDB/report export manager.
- `examples/`: runnable example snippets.
- `tests/`: test stubs.

## Roadmap

1. Stage-1 Python SDF Prototype
2. Stage-2 Mesh-to-SDF + Geometry Validation
3. Stage-3 PicoGK/OpenVDB production backend

## Citation / References

- [LEAP71/PicoGK](https://github.com/leap71/PicoGK)
- [LEAP71/PicoGKRuntime](https://github.com/leap71/PicoGKRuntime)
- [LEAP71/LEAP71_ShapeKernel](https://github.com/leap71/LEAP71_ShapeKernel)
- [fogleman/sdf](https://github.com/fogleman/sdf)
- [pschou/py-sdf](https://github.com/pschou/py-sdf)
- [marian42/mesh_to_sdf](https://github.com/marian42/mesh_to_sdf)
- [sxyu/sdf (pysdf)](https://github.com/sxyu/sdf)
- [zzilch/Mesh2Volume](https://github.com/zzilch/Mesh2Volume)
- [AcademySoftwareFoundation/openvdb](https://github.com/AcademySoftwareFoundation/openvdb)
- [facebookresearch/iSDF](https://github.com/facebookresearch/iSDF)
- [GCoiffier/1-Lipschitz-Neural-Distance-Fields](https://github.com/GCoiffier/1-Lipschitz-Neural-Distance-Fields)
- [AkmalBakar/neural_sdf](https://github.com/AkmalBakar/neural_sdf)
