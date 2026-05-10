KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT = """
You are generating LabCEM domain knowledge artifacts.
Rules:
- Output JSON only.
- Do not fabricate formulas not present in source text.
- If inferred, put into implementation_hints with lower confidence.
- Focus on formulas, parameters, curves, geometry rules, manufacturing constraints.
- Do not propose direct STL/OBJ export.
- Do not modify labcem/core, GUI, or production components.
""".strip()

KNOWLEDGE_EXTRACTION_USER_TEMPLATE = """
Kernel: {kernel_id}
Component: {component_type}
Source ID: {source_id}
Source Text:\n{source_text}
Return JSON that matches KNOWLEDGE_EXTRACTION_SCHEMA.
""".strip()

SCHEMA_GENERATION_SYSTEM_PROMPT = """
Generate LabCEM component schema JSON for CLI/GUI.
Include bilingual aliases, required/default/unit fields.
Do not write code. Output JSON only.
""".strip()

SCHEMA_GENERATION_USER_TEMPLATE = """
Kernel: {kernel_id}
Component: {component_type}
Knowledge cards:\n{knowledge_cards}
Formula cards:\n{formula_cards}
Rules:\n{rules}
Return JSON matching COMPONENT_SCHEMA_SCHEMA.
""".strip()

CODEGEN_SYSTEM_PROMPT = """
Generate proposed LabCEM code only.
Constraints:
- Builder must inherit ComponentBuilder.
- build() must call backend methods only (e.g., backend.build_waveguide_sdf(spec)).
- No import labcem.gui / labcem.cli.
- No mesh.export() and no direct STL/OBJ writing.
- Do not modify labcem.core.
- Add '# AUTO-GENERATED PROPOSAL - REVIEW BEFORE APPLY' header.
Output JSON only.
""".strip()

CODEGEN_USER_TEMPLATE = """
Kernel: {kernel_id}
Component: {component_type}
Schema:\n{schema_json}
Knowledge cards:\n{knowledge_cards}
Formula cards:\n{formula_cards}
Rules:\n{rules}
Codegen rules:\n{codegen_rules}
Return JSON matching CODEGEN_SCHEMA.
""".strip()

REVIEW_SYSTEM_PROMPT = """
Review proposed LabCEM code against codegen rules.
Output review JSON only and do not rewrite code.
LLM review cannot replace static review.
""".strip()

REVIEW_USER_TEMPLATE = """
Kernel: {kernel_id}
Component: {component_type}
Code:\n{code_text}
Return JSON matching REVIEW_SCHEMA.
""".strip()
