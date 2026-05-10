from labcem.l1.geometry import GeometryObject
from labcem.l1.mesh_export import extract_mesh
from labcem.l1.voxel_field import SDFGrid

from .cadquery_backend import build_cad_geometry
from .mesh_loft_backend import build_waveguide_loft
from .mesh_backend import validate_mesh_with_trimesh
from .operation_graph import OperationGraph
from .sdf_backend import apply_sdf_operations, build_sdf_from_params


class GeometryKernelRouter:
    def execute(self, graph: OperationGraph, voxel_resolution=24):
        geometry = build_cad_geometry(graph.parameters)
        shape = str(graph.parameters.get("shape", "")).lower()
        use_sdf = bool(graph.parameters.get("experimental_sdf", False))
        if shape in ("waveguide", "horn") and not use_sdf:
            loft = build_waveguide_loft(graph.parameters)
            return {
                "geometry": geometry if isinstance(geometry, GeometryObject) else GeometryObject(kind="unknown", params={}),
                "grid": None,
                "verts": loft["verts"],
                "faces": loft["faces"],
                "operation_log": ["mesh_loft(section_loft)"],
                "loft_validation": loft["validation"],
                "profile_samples_full": loft["profile_samples"],
                "profile_samples_key": loft["profile_samples_key"],
                "geometry_backend": loft["geometry_backend"],
                "waveguide_surface": loft["waveguide_surface"],
                "marching_cubes_used": loft["marching_cubes_used"],
                "section_count": loft["section_count"],
            }
        base_sdf, span = build_sdf_from_params(graph.parameters)
        sdf_fn, op_log = apply_sdf_operations(base_sdf, graph.operations)
        grid = SDFGrid(resolution=voxel_resolution, span=span).sample(sdf_fn)
        verts, faces, _normals, _vals = extract_mesh(grid.values)
        return {
            "geometry": geometry if isinstance(geometry, GeometryObject) else GeometryObject(kind="unknown", params={}),
            "grid": grid,
            "verts": verts,
            "faces": faces,
            "operation_log": op_log,
            "geometry_backend": "sdf_marching_cubes",
            "waveguide_surface": "sdf_iso_surface",
            "marching_cubes_used": True,
        }

    def validate_mesh(self, stl_path):
        return validate_mesh_with_trimesh(stl_path)

