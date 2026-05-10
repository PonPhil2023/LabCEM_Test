from labcem.shapes.waveguide import create_waveguide
from labcem.validation.validator import validate_geometry
from labcem.export.exporter import export_stl

spec = {
    "type": "waveguide",
    "throat_diameter": 25.0,
    "mouth_width": 180.0,
    "mouth_height": 120.0,
    "depth": 90.0,
    "directivity_h": 90.0,
    "directivity_v": 60.0,
    "bandwidth": (1000.0, 18000.0),
    "wall_thickness": 3.0,
    "flange_thickness": 8.0,
}

model = create_waveguide(spec)
report = validate_geometry(model, spec)
print(report["ok"])
export_stl(model, "outputs/waveguide_from_example.stl")
