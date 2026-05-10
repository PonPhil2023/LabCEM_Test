from dataclasses import dataclass


@dataclass
class GeometryObject:
    kind: str
    params: dict


def cylinder(radius: float, height: float, center=(0, 0, 0), direction=(0, 0, 1), segments: int = 64) -> GeometryObject:
    return GeometryObject(
        kind="cylinder",
        params={
            "radius": radius,
            "height": height,
            "center": center,
            "direction": direction,
            "segments": segments,
        },
    )
