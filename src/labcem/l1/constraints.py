from .geometry import GeometryObject


def validate_constraints(geometry: GeometryObject, constraints: dict):
    violations = []
    min_wall = constraints.get("min_wall_thickness", 0)
    if geometry.kind == "cylinder":
        if geometry.params["radius"] <= 0 or geometry.params["height"] <= 0:
            violations.append("cylinder dimensions must be positive")
        if geometry.params["radius"] < min_wall:
            violations.append("radius violates min_wall_thickness")
    return violations
