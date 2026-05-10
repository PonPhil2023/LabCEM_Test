from __future__ import annotations

import argparse
import json
from pathlib import Path

from labcem.agents.agent_pipeline import DomainAgentPipeline
from labcem.orchestrator import LabCEMOrchestrator


def _print(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _add_agent_mode_arg(p):
    p.add_argument("--agent-mode", default="hybrid", choices=["rules", "llm", "hybrid"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LabCEM generation pipeline")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="One-shot generation mode")
    p_run.add_argument("--spec", required=True)
    p_run.add_argument("--domain", default="general")
    p_run.add_argument("--kernel", default="acoustic_kernel")
    p_run.add_argument("--backend", default="python_sdf")
    p_run.add_argument("--component", default="waveguide")
    p_run.add_argument("--knowledge-root", default="knowledge/domains")
    p_run.add_argument("--output", default="outputs/generated_geometry.json")
    p_run.add_argument("--model-path", default=None)

    p_ingest = sub.add_parser("ingest", help="Knowledge ingestion")
    ingest_sub = p_ingest.add_subparsers(dest="ingest_cmd")

    p_ingest_add = ingest_sub.add_parser("add")
    p_ingest_add.add_argument("--kernel", required=True)
    p_ingest_add.add_argument("--source", action="append", required=True)

    p_ingest_extract = ingest_sub.add_parser("extract")
    p_ingest_extract.add_argument("--kernel", required=True)
    p_ingest_extract.add_argument("--source-id", required=True)
    p_ingest_extract.add_argument("--component", required=True)
    _add_agent_mode_arg(p_ingest_extract)

    p_kernel = sub.add_parser("kernel", help="Kernel utilities")
    kernel_sub = p_kernel.add_subparsers(dest="kernel_cmd")
    p_kernel_schema = kernel_sub.add_parser("schema")
    p_kernel_schema.add_argument("--kernel", required=True)
    p_kernel_schema.add_argument("--component", required=True)
    _add_agent_mode_arg(p_kernel_schema)

    p_agent = sub.add_parser("agent", help="Agent utilities")
    agent_sub = p_agent.add_subparsers(dest="agent_cmd")
    p_agent_propose = agent_sub.add_parser("propose-code")
    p_agent_propose.add_argument("--kernel", required=True)
    p_agent_propose.add_argument("--component", required=True)
    _add_agent_mode_arg(p_agent_propose)

    p_agent_review = agent_sub.add_parser("review")
    p_agent_review.add_argument("--kernel", required=True)
    p_agent_review.add_argument("--component", required=True)
    _add_agent_mode_arg(p_agent_review)

    agent_sub.add_parser("llm-status")

    args = parser.parse_args()

    if args.cmd == "run":
        domain = "acoustic" if (args.domain or "general").lower() == "general" else args.domain
        app = LabCEMOrchestrator(knowledge_root=args.knowledge_root, model_path=args.model_path)
        result = app.run_from_prompt(prompt=args.spec, domain=domain, kernel=args.kernel, backend=args.backend, output=args.output, component_type=args.component)
        _print(result)
        return

    pipeline = DomainAgentPipeline()

    if args.cmd == "ingest" and args.ingest_cmd == "add":
        files = [s for s in args.source if Path(s).is_file()]
        dirs = [s for s in args.source if Path(s).is_dir()]
        outputs, messages = [], []
        ok = True
        if files:
            r = pipeline.import_documents(args.kernel, files)
            outputs += r.get("outputs", [])
            messages.append(r.get("message", ""))
            ok = ok and r.get("ok", False)
        for d in dirs:
            r = pipeline.import_github_repo(args.kernel, d)
            outputs += r.get("outputs", [])
            messages.append(r.get("message", ""))
            ok = ok and r.get("ok", False)
        _print({"ok": ok, "message": " | ".join(messages), "outputs": outputs})
        return

    if args.cmd == "ingest" and args.ingest_cmd == "extract":
        _print(pipeline.extract_knowledge(args.kernel, args.source_id, args.component, mode=args.agent_mode))
        return

    if args.cmd == "kernel" and args.kernel_cmd == "schema":
        _print(pipeline.generate_schema(args.kernel, args.component, mode=args.agent_mode))
        return

    if args.cmd == "agent" and args.agent_cmd == "propose-code":
        _print(pipeline.propose_code(args.kernel, args.component, mode=args.agent_mode))
        return

    if args.cmd == "agent" and args.agent_cmd == "review":
        _print(pipeline.review_proposal(args.kernel, args.component, mode=args.agent_mode))
        return

    if args.cmd == "agent" and args.agent_cmd == "llm-status":
        _print(pipeline.llm_status())
        return

    parser.print_help()


if __name__ == "__main__":
    main()
