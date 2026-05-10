from labcem.orchestrator import LabCEMOrchestrator

app = LabCEMOrchestrator(knowledge_root="knowledge/domains")
result = app.run(
    spec="Generate a cylindrical component for quick prototype validation.",
    domain="general",
    output_path="outputs/example_geometry.json",
)
print(result)
