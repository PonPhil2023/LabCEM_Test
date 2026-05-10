def validate_generated_instruction(instruction: dict) -> None:
    if "shape" not in instruction:
        raise ValueError("Generated instruction must include 'shape'.")
    if instruction["shape"] not in ("cylinder", "torus", "hex_bolt", "sphere", "waveguide", "horn"):
        raise ValueError("Supported shapes: cylinder, torus, hex_bolt, sphere, waveguide, horn.")
    backend = instruction.get("backend", "sdf")
    if backend not in ("sdf", "cadquery", "build123d", "mesh"):
        raise ValueError("Supported backends: sdf, cadquery, build123d, mesh.")
