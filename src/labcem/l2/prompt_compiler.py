def compile_prompt(spec: str, knowledge_excerpt: str, constraints: dict, attachment_excerpt: str = "", research_excerpt: str = "") -> str:
    extra = ""
    if attachment_excerpt:
        extra += "\nAttachment Knowledge:\n{0}\n".format(attachment_excerpt)
    if research_excerpt:
        extra += "\nWeb Research Excerpt:\n{0}\n".format(research_excerpt)
    return (
        "[SYSTEM]\n"
        "You are a computational engineering model planner and geometry instruction generator.\n"
        "Always map user intent to manufacturable geometry primitives and operations.\n"
        "Knowledge:\n{0}\n"
        "Constraints:\n{1}\n"
        "{2}\n"
        "[USER]\n"
        "{3}\n"
        "[OUTPUT]\n"
        "JSON instruction for geometry generation."
    ).format(knowledge_excerpt, constraints, extra, spec)
