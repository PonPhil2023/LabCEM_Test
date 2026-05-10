KNOWLEDGE_EXTRACTION_SCHEMA = {
    "title": "knowledge_extraction",
    "type": "object",
    "required": ["ok", "domain", "component_type", "knowledge_cards", "formula_cards", "rules", "warnings", "source_coverage_summary"],
}

COMPONENT_SCHEMA_SCHEMA = {
    "title": "component_schema",
    "type": "object",
    "required": ["ok", "kernel_id", "domain", "component_type", "display_name", "aliases", "parameters", "targets", "manufacturing", "generated_from", "warnings"],
}

CODEGEN_SCHEMA = {
    "title": "codegen_schema",
    "type": "object",
    "required": ["ok", "component_file", "solver_file", "test_file", "notes", "warnings"],
}

REVIEW_SCHEMA = {
    "title": "review_schema",
    "type": "object",
    "required": ["ok", "summary", "issues", "recommended_changes", "risk_level", "approve_for_static_review"],
}
