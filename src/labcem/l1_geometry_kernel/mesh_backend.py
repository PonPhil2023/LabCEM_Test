def validate_mesh_with_trimesh(stl_path):
    try:
        import trimesh
    except Exception:
        return {"enabled": False, "ok": True, "reason": "trimesh_not_installed"}

    mesh = trimesh.load_mesh(stl_path)
    return {
        "enabled": True,
        "ok": bool(mesh.is_watertight),
        "faces": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "is_watertight": bool(mesh.is_watertight),
        "euler_number": int(mesh.euler_number),
    }

