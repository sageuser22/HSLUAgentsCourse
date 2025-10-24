# bp_assistant_seq.py
# 3-agent sequential handoff to draft a grant proposal from two input .txt files
# - Tools: read_txt (read local .txt), save_proposal (write final Markdown)
# - Agents:
#     1) requirements_agent -> analyzes grant requirements
#     2) drafting_agent     -> drafts proposal
#     3) review_agent       -> reviews & saves final proposal
#
# Usage:
#   poetry run python grant_handoff_agents.py \
#       --idea-file ./project_idea.txt \
#       --grant-file ./grant_requirements.txt \
#       --out-dir ./submission_kit_handoff

import argparse
import os, sys
from pathlib import Path

# --- Load API key & model like simple_fit_agent_sdk.py ---
from dotenv import load_dotenv
load_dotenv()  # optional; will read OPENAI_API_KEY, OPENAI_MODEL if present
try:
    import config
    if getattr(config, "OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        print("✅ Loaded OpenAI API key from config.py")
    else:
        raise AttributeError("OPENAI_API_KEY not found in config.py")
except Exception:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if os.getenv("OPENAI_API_KEY"):
            print("✅ Loaded OpenAI API key from .env file")
        else:
            raise EnvironmentError("OPENAI_API_KEY missing from .env")
    except Exception as e:
        print(f"⚠️  Failed to load API key: {e}")
        sys.exit(1)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# --- OpenAI Agents SDK ---
from agents import Agent, Runner, function_tool, handoff


# -------------------------
# Tools
# -------------------------

@function_tool
def read_txt(path: str) -> str:
    """Read a local UTF-8 .txt file and return its contents (stripped)."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if p.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file: {path}")
    return p.read_text(encoding="utf-8").strip()


@function_tool
def save_proposal(out_dir: str, draft_text_md: str) -> str:
    """Save the final proposal Markdown to <out_dir>/proposal.md."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "proposal.md"
    path.write_text(draft_text_md, encoding="utf-8")
    return f"Saved proposal to {str(path.resolve())}"



# -------------------------
# Agents
# -------------------------

# Agent 3: Reviewer (final step; no further handoffs)
review_agent = Agent(
    name="review_agent",
    model=MODEL,
    instructions=(
        "You are the Final Reviewer for a grant application proposal. "
        "You receive: `draft_text_md` and `out_dir` in the handoff message. "
        "Tasks:\n"
        "1) Review for clarity, alignment with requirements, and coherence. "
        "   Fix grammar, tighten language, ensure the draft is cohesive and persuasive. "
        "2) Keep the final output as Markdown. "
        "3) Call `save_proposal(out_dir, draft_text_md=<final edited markdown>)`. "
        "4) After saving, print a short friendly confirmation for the console."
    ),
    tools=[save_proposal],
)

# Agent 2: Drafter (hands off to Reviewer)
drafting_agent = Agent(
    name="drafting_agent",
    model=MODEL,
    instructions=(
        "You are the Senior Grant Writer. You receive from the analyst: "
        "`analysis_summary` (of the grant), the `user_idea` (project description), and `out_dir`.\n"
        "Tasks:\n"
        "1) Write a compelling full grant proposal in Markdown, covering typical sections:\n"
        "   - Executive Summary\n"
        "   - Need Statement / Problem\n"
        "   - Goals & Objectives\n"
        "   - Program Description & Activities\n"
        "   - Target Population & Impact\n"
        "   - Implementation Timeline\n"
        "   - Evaluation Plan (metrics & methods)\n"
        "   - Organizational Capacity\n"
        "   - Budget Summary & Justification (high-level)\n"
        "   - Sustainability & Risk Mitigation\n"
        "   - Alignment with Funder Priorities\n"
        "   Ensure alignment with the analysis (word/page limits, required sections).\n"
        "2) When the draft is COMPLETE, you MUST call `handoff_to_reviewer`.\n"
        "3) In the handoff `message`, include:\n"
        "   - `draft_text_md`: the full Markdown proposal you wrote.\n"
        "   - `out_dir`: the same output directory you received."
    ),
    handoffs=[review_agent]
)


# Agent 1: Requirements Analyst (first step; hands off to Drafter)
requirements_agent = Agent(
    name="requirements_agent",
    model=MODEL,
    instructions=(
        "You are the Requirements Analyst. You start the process.\n"
        "Inputs available via the user message: `GRANT_FILE_PATH`, `IDEA_FILE_PATH`, `OUT_DIR`.\n"
        "Tasks:\n"
        "1) Call `read_txt(GRANT_FILE_PATH)` to read the grant requirements text.\n"
        "2) Call `read_txt(IDEA_FILE_PATH)` to read the project idea text.\n"
        "3) Analyze the grant to extract practical constraints and guidance for drafting, e.g.:\n"
        "   - Eligibility criteria\n"
        "   - Funding priorities & prohibited activities\n"
        "   - Required sections & formatting (word/page limits, fonts, margins)\n"
        "   - Submission deadlines or timeline expectations\n"
        "   - Evaluation & reporting expectations\n"
        "4) Produce a concise `analysis_summary` that the drafter can follow as a checklist.\n"
        "5) You MUST call `handoff_to_drafter` with a `message` that includes:\n"
        "   - `analysis_summary`\n"
        "   - `user_idea` (the project idea text)\n"
        "   - `out_dir` (the output directory)\n"
        "Do NOT save files in this step."
    ),
    tools=[
        read_txt,
    ],
    handoffs=[drafting_agent],
)


# -------------------------
# CLI
# -------------------------

def build_user_message(idea_path: str, grant_path: str, out_dir: str) -> str:
    # Single message that seeds agent 1 with all paths & context (like your simple_fit_agent pattern)
    return (
        "Begin the 3-agent grant proposal workflow.\n"
        f"GRANT_FILE_PATH: {grant_path}\n"
        f"IDEA_FILE_PATH: {idea_path}\n"
        f"OUT_DIR: {out_dir}\n"
        "Proceed with the steps."
    )


def _validate_txt_file_or_die(path: str, label: str) -> None:
    p = Path(path)
    if not p.exists() or not p.is_file():
        print(f"❌ {label} not found: {path}")
        sys.exit(1)
    if p.suffix.lower() != ".txt":
        print(f"❌ {label} must be a .txt file: {path}")
        sys.exit(1)
    if not p.read_text(encoding="utf-8").strip():
        print(f"❌ {label} is empty: {path}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="3-Agent Handoff Grant Proposal (OpenAI Agents SDK)")
    parser.add_argument("--idea-file", required=True, help="Path to project idea .txt")
    parser.add_argument("--grant-file", required=True, help="Path to grant requirements .txt")
    parser.add_argument("--out-dir", default="./submission_kit_handoff", help="Output directory for final proposal")
    args = parser.parse_args()

    _validate_txt_file_or_die(args.idea_file, "Idea file")
    _validate_txt_file_or_die(args.grant_file, "Grant file")

    msg = build_user_message(args.idea_file, args.grant_file, args.out_dir)

    run_fn = getattr(Runner, "run_sync", None) or getattr(Runner, "run", None)
    if not run_fn:
        raise RuntimeError("Agents SDK Runner has no run/run_sync method.")

    print(
        f"\n🚀 Starting 3-agent handoff...\n"
        f"Model: {MODEL}\n"
        f"Idea: {args.idea_file}\n"
        f"Grant: {args.grant_file}\n"
        f"Out Dir: {args.out_dir}\n"
    )

    # We call only the first agent; SDK follows handoffs automatically
    result = run_fn(requirements_agent, msg)

    # Console-friendly summary (SDK return shapes vary)
    text = getattr(result, "final_output", None) or getattr(result, "output_text", None)
    if not text and hasattr(result, "messages"):
        msgs = result.messages
        if msgs:
            last = msgs[-1]
            text = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else None)

    print("\n=== DONE ===\n")
    print(text or f"Run completed. (Check '{args.out_dir}/proposal.md')")


if __name__ == "__main__":
    main()
