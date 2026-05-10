from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..export.export_manager import ExportManager


class BuildPipeline:
    def __init__(self, kernel_manager, backend_registry):
        self.kernel_manager = kernel_manager
        self.backend_registry = backend_registry
        self.exporter = ExportManager()

    def run(
        self,
        spec: Dict[str, Any],
        kernel_id: str,
        backend_id: str,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        kernel = self.kernel_manager.get_active_kernel(kernel_id)
        kernel.validate_spec(spec)

        component_type = spec.get("component_type", "waveguide")
        builder = kernel.get_component_builder(component_type)
        solved_spec = builder.solve_parameters(spec)
        public_spec = {k: v for k, v in solved_spec.items() if not str(k).startswith("__")}

        requested_backend = backend_id
        effective_backend = backend_id
        backend = self.backend_registry.create(requested_backend)
        backend_warning = None

        # LEAP71-style resilience: if selected backend cannot build this component,
        # fallback to python_sdf instead of hard failure.
        try:
            model = builder.build(solved_spec, backend)
        except Exception as exc:
            if "build_waveguide_sdf" in str(exc) or "attribute" in str(exc).lower() or "not implemented" in str(exc).lower():
                fallback_backend_id = "python_sdf"
                backend = self.backend_registry.create(fallback_backend_id)
                effective_backend = fallback_backend_id
                backend_warning = f"Backend '{requested_backend}' is not ready for {component_type}; fallback to '{fallback_backend_id}'."
                model = builder.build(solved_spec, backend)
            else:
                raise

        mesh = backend.to_mesh(model, solved_spec)
        mesh = backend.repair_mesh(mesh)
        geometry_validation = backend.validate_geometry(mesh, solved_spec)

        builder_validation = builder.validate(model, solved_spec)
        builder_meta = builder.metadata(model, solved_spec)
        kernel_meta = kernel.export_metadata(model, solved_spec)

        out_json = Path(output or "outputs/generated_geometry.json")
        run_dir = out_json.parent / "latest_run"
        run_dir.mkdir(parents=True, exist_ok=True)

        stl_name = f"{component_type}_demo.stl"
        obj_name = f"{component_type}_demo.obj"
        mesh_stl = self.exporter.export_mesh(mesh, str(run_dir / stl_name))
        mesh_obj = self.exporter.export_mesh(mesh, str(run_dir / obj_name))

        self.exporter.export_json(public_spec, str(run_dir / "design_spec.json"))
        self.exporter.export_json(geometry_validation, str(run_dir / "validation_report.json"))

        metadata = {
            "builder": builder_meta,
            "kernel": kernel_meta,
            "materials": kernel.get_default_materials(),
            "manufacturing_rules": kernel.get_manufacturing_rules(),
        }
        if backend_warning:
            metadata["backend_warning"] = backend_warning
        self.exporter.export_json(metadata, str(run_dir / "metadata.json"))

        build_report = {
            "intent": f"create_{component_type}",
            "kernel_id": kernel_id,
            "backend": requested_backend,
            "effective_backend": effective_backend,
            "shape": component_type,
            "topology": geometry_validation.get("topology", {}),
            "validation_summary": geometry_validation.get("validation_summary", {}),
            "export_status": {
                "stl": "ok",
                "obj": "ok",
                "step": "not_implemented",
                "3mf": "not_implemented",
            },
            "builder_validation": builder_validation,
            "input_requirements": public_spec,
        }
        if backend_warning:
            build_report["warnings"] = [backend_warning]
        self.exporter.export_json(build_report, str(run_dir / "build_report.json"))

        result_payload = {
            "spec": public_spec,
            "mesh_stl": str(mesh_stl),
            "mesh_obj": str(mesh_obj),
            "validation": geometry_validation,
            "build_report": build_report,
            "metadata": metadata,
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "units": "mm",
            "family": public_spec.get("family", public_spec.get("profile_family", "tritonia")),
            "throat_diameter": float(public_spec.get("throat_diameter", 0.0)),
            "mouth_width": float(public_spec.get("mouth_width", 0.0)),
            "mouth_height": float(public_spec.get("mouth_height", 0.0)),
            "depth": float(public_spec.get("depth", 0.0)),
            "profile_family": public_spec.get("profile_family", public_spec.get("family", "tritonia")),
            "validation_summary": geometry_validation.get("validation_summary", {}),
        }
        self.exporter.export_json(result_payload, str(out_json))

        steps = [
            {"layer": "L0", "status": "done", "package": "prompt/spec parser", "action": "design intent parsed"},
            {"layer": "L1", "status": "done", "package": "domain kernel", "action": "component parameters solved"},
            {"layer": "L2", "status": "done", "package": "backend", "action": "SDF model and mesh generated"},
            {"layer": "L3", "status": "done", "package": "validation", "action": "geometry validated"},
            {"layer": "L4", "status": "done", "package": "export", "action": "artifacts exported"},
        ]

        reason = "core_pipeline" if not backend_warning else "core_pipeline_fallback"
        model_mode = model.get("mode") if isinstance(model, dict) else None
        waveguide_surface = "ath_like_superellipse" if model_mode == "mesh" else ("implicit_sdf" if component_type == "waveguide" else "component_defined")
        return {
            "output": str(out_json),
            "mesh_stl": str(mesh_stl),
            "mesh_obj": str(mesh_obj),
            "mesh_step": None,
            "mesh_3mf": None,
            "output_dir": str(run_dir),
            "shape": component_type,
            "source": "labcem_core_domain_kernel",
            "backend": requested_backend,
            "effective_backend": effective_backend,
            "cli_status": {"available": True, "ok": True, "exit_code": 0, "reason": reason, "mode": "internal"},
            "cli_raw_output": "BuildPipeline executed." + (f" {backend_warning}" if backend_warning else ""),
            "operation_graph": ["validate_spec", "solve_parameters", "build", "to_mesh", "repair", "validate", "export"],
            "operation_log": ["BuildPipeline completed"],
            "voxel_resolution": int(public_spec.get("resolution", 36)),
            "voxels": [],
            "sdf_grid": None,
            "geometry_backend": effective_backend,
            "waveguide_surface": waveguide_surface,
            "marching_cubes_used": effective_backend == "python_sdf" and model_mode != "mesh",
            "mesh_validation": geometry_validation,
            "build_report": build_report,
            "topology": geometry_validation.get("topology", {}),
            "profile_samples": [],
            "profile_samples_count": 0,
            "mesh_verts": mesh.vertices.tolist(),
            "mesh_faces": mesh.faces.tolist(),
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "units": "mm",
            "family": public_spec.get("family", public_spec.get("profile_family", "tritonia")),
            "throat_diameter": float(public_spec.get("throat_diameter", 0.0)),
            "mouth_width": float(public_spec.get("mouth_width", 0.0)),
            "mouth_height": float(public_spec.get("mouth_height", 0.0)),
            "depth": float(public_spec.get("depth", 0.0)),
            "profile_family": public_spec.get("profile_family", public_spec.get("family", "tritonia")),
            "validation_summary": geometry_validation.get("validation_summary", {}),
            "pipeline_steps": steps,
            "label9_summary": f"{component_type} generated by {kernel_id}/{effective_backend}",
        }
