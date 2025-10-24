# bp_assistant_orc.py
# SIMPLIFIED VERSION - NO GUARDRAILS OR QUALITY CHECKS
#
# Inputs: user idea from --idea-file .txt, grant description from --grant-file .txt
# Outputs: submission kit folder with strategy note, outline, and draft narrative

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

# --- Load OpenAI API key from config.py or .env ---
try:
    import config  # Optional local file with: OPENAI_API_KEY = "sk-..."

    if getattr(config, "OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        print("✅ Loaded OpenAI API key from config.py")
    else:
        raise AttributeError("OPENAI_API_KEY not found in config.py")
except Exception:
    try:
        from dotenv import load_dotenv  # pip install python-dotenv

        load_dotenv()
        if os.getenv("OPENAI_API_KEY"):
            print("✅ Loaded OpenAI API key from .env file")
        else:
            raise EnvironmentError("OPENAI_API_KEY missing from .env")
    except Exception as e:
        print(f"⚠️  Failed to load API key: {e}")
        print("    Create config.py with OPENAI_API_KEY = 'sk-...' or a .env with OPENAI_API_KEY=sk-...")
        sys.exit(1)

# OpenAI Agents SDK
from agents import Agent, Runner, function_tool, WebSearchTool
from agents.model_settings import ModelSettings


# -----------------------------
# Data shapes we pass between agents
# -----------------------------
class GrantRequirements(BaseModel):
    name: str = ""
    funder: str = ""
    deadline_utc: Optional[str] = None
    currency: str = "USD"
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    eligibility_summary: str = ""
    prohibited: List[str] = []
    required_sections: List[str] = []
    word_limits: Dict[str, int] = {}
    # 'rubric' field removed as it's part of quality checks
    attachments: List[str] = []


class StrategyNote(BaseModel):
    thesis: str
    proof_points: List[str]
    outcomes: List[str]
    value_for_money: str


class OutlineItem(BaseModel):
    section: str
    target_words: int
    key_messages: List[str] = []


class Outline(BaseModel):
    items: List[OutlineItem]


class SectionDraft(BaseModel):
    section: str
    headline: str
    body: str


class SearchSnippet(BaseModel):
    source: str
    snippet: str


class NoveltyReport(BaseModel):
    novelty_score: int  # Score from 0 (not novel) to 100 (highly novel)
    key_competitors: List[str] = []
    key_differentiators: List[str] = []
    summary: str = "Brief rationale for the score and findings."
    search_snippets: List[SearchSnippet] = []


# -----------------------------
# Deterministic tools the agent can call
# -----------------------------

@function_tool
def read_local_file(path: str) -> str:
    """
    Read a local UTF-8 text file and return its contents. Must be .txt.
    (Simplified: No size or content moderation guardrails).
    """
    p = Path(path)

    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Grant file not found: {path}")

    if p.suffix.lower() != ".txt":
        raise ValueError("Grant file must be a .txt")

    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")

    return content


@function_tool
def merge_sections_to_markdown(section_drafts: List[SectionDraft]) -> str:
    """Deterministically merge SectionDrafts (list of dicts) into a single Markdown narrative."""
    parts = []
    for sd in section_drafts:
        if isinstance(sd, BaseModel):
            title = (sd.headline or sd.section or "Section").strip()
            body = (sd.body or "").strip()
        else:
            title = (sd.get("headline") or sd.get("section") or "Section").strip()
            body = (sd.get("body") or "").strip()
        parts.append(f"## {title}\n\n{body}")
    return "\n\n".join(parts).strip()


@function_tool
def save_submission_kit(
        out_dir: str,
        strategy_note: StrategyNote,
        outline: Outline,
        novelty_report: NoveltyReport,
        narrative_md: str,
) -> str:
    """Write files to a folder so the user can submit easily."""

    def _to_str(x):
        if isinstance(x, BaseModel):
            return x.model_dump_json(indent=2)
        if isinstance(x, list) and x and isinstance(x[0], BaseModel):
            return json.dumps([item.model_dump() for item in x], ensure_ascii=False, indent=2)
        if isinstance(x, (dict, list)):
            return json.dumps(x, ensure_ascii=False, indent=2)
        return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, indent=2)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "strategy_note.json").write_text(_to_str(strategy_note), encoding="utf-8")
    (out / "outline.json").write_text(_to_str(outline), encoding="utf-8")
    (out / "novelty_report.json").write_text(_to_str(novelty_report), encoding="utf-8")
    (out / "narrative.md").write_text(_to_str(narrative_md), encoding="utf-8")
    # Removed rubric_scorecard.json and compliance_checklist.json

    return f"Wrote files to {str(out.resolve())}"


# -----------------------------
# Specialized agents
# -----------------------------

MODEL = "gpt-5"  # Using the model from the original script

requirements_agent = Agent(
    name="requirements_agent",
    model=MODEL,
    instructions=(
        "You extract a structured requirement summary from a grant call. "
        "Return a complete JSON using the GrantRequirements schema: "
        "{name,funder,deadline_utc,currency,min_amount,max_amount,eligibility_summary,"
        "prohibited,required_sections,word_limits,attachments}. "  # Rubric removed
        "Be precise. Infer reasonable defaults only when clearly implied."
    ),
)

strategy_agent = Agent(
    name="strategy_agent",
    model=MODEL,
    instructions=(
        "You are a senior grant strategist. Given the applicant's idea, the grant requirements, "
        "and a NoveltyReport, write a concise Strategy Note as JSON (StrategyNote schema): "
        "{thesis,proof_points[],outcomes[],value_for_money}. "
        "Use the NoveltyReport to emphasize key differentiators and position the idea against competitors. "
        "Keep it under 300 words overall. No fluff."
    ),
)

outline_agent = Agent(
    name="outline_agent",
    model=MODEL,
    instructions=(
        "You create a section-by-section outline aligned to required_sections and word_limits. "
        "Return Outline JSON: items=[{section,target_words,key_messages[]}]. "
        "Split the total words sensibly if limits are missing; always set target_words."
    ),
)

draft_agent = Agent(
    name="draft_agent",
    model=MODEL,
    instructions=(
        "You write crisp, funder-aligned prose for a single section. "
        "For the given OutlineItem, produce a SectionDraft JSON: {section,headline,body}. "
        "Prefer active voice; avoid ungrounded claims."
    ),
    # Removed word_count tool
)

# fit_gate_agent, scorer_agent, compliance_agent, inclusivity_agent, fact_check_agent, refine_agent removed

novelty_agent = Agent(
    name="novelty_agent",
    model=MODEL,
    instructions=(
        "You are a market and research analyst. Your job is to assess the novelty "
        "of a user's idea given the grant's context. "
        "1. Formulate 2-3 concise search queries to find competitors or similar published work. "
        "2. Call the provided `WebSearchTool` for each query to gather intelligence. "
        "   If the tool returns raw text, convert it into a list of snippet dicts of the form "
        "   [{'source':'unknown','snippet':'<short extract>'}]. If it returns structured results, use them directly."
        "3. Analyze the search snippets you formed/received. "
        "4. Return a `NoveltyReport` JSON. Be objective. "
        "   - Set `novelty_score` (0-100). "
        "   - List 2-3 `key_competitors` or similar projects. "
        "   - List 2-3 `key_differentiators` for the user's idea. "
        "   - Write a brief `summary`. "
        "   - **Crucially, you MUST include the raw search snippets** you analyzed in the `search_snippets` field."
    ),
    tools=[WebSearchTool()],
    model_settings=ModelSettings(tool_choice="auto"),
)

# -----------------------------
# Orchestrator agent (calls the specialists & tools)
# -----------------------------

orchestrator = Agent(
    name="orchestrator",
    model=MODEL,
    instructions=(
        "You are the grant writing coordinator. You MUST follow this simplified execution plan strictly. "
        "Inputs are provided in the message content: NOW, GRANT_FILE_PATH, OUTPUT_DIR, and USER_IDEA.\n\n"

        "--- PHASE 1: INTAKE (Sequential) ---\n"
        "1) Call `read_local_file(GRANT_FILE_PATH)` to load the grant call text.\n"
        "2) Call `extract_requirements` with the grant call text to get `GrantRequirements` JSON.\n\n"

        "--- PHASE 2: STRATEGY & DRAFTING (Parallel & Sequential) ---\n"
        "3) Call `novelty_check` (user idea, requirements) to get the `NoveltyReport` JSON. "
        "   (Store as `novelty_report`).\n"
        "4) **[Parallel Task]** These two tasks can run in parallel. Wait for both to complete:\n"
        "   a) Call `synthesize_strategy` (idea, requirements, novelty_report) -> `StrategyNote` (Store as `strategy_note`)\n"
        "   b) Call `make_outline` (requirements, idea) -> `Outline` (Store as `outline`)\n"
        "5) **[Parallel Task]** For EACH item in the `Outline`, call `draft_sections` in parallel "
        "   to get a list of `SectionDraft` JSONs. Wait for ALL drafts to be returned. "
        "   (Store as `current_draft_list`).\n\n"

        "--- PHASE 3: FINAL PACKAGING (Sequential) ---\n"
        "6) Call `merge_sections_to_markdown` (`current_draft_list`) -> `narrative_final`.\n"
        "7) Call `save_submission_kit`(out_dir=OUTPUT_DIR, strategy_note=strategy_note, outline=outline, "
        "     novelty_report=novelty_report, narrative_md=narrative_final).\n"
        "8) Finally, print a short human-readable summary of the process and the output folder path."
    ),
    tools=[
        read_local_file,
        merge_sections_to_markdown,
        save_submission_kit,
        requirements_agent.as_tool(
            tool_name="extract_requirements",
            tool_description="Extracts and structures the grant call requirements into JSON.",
        ),
        novelty_agent.as_tool(
            tool_name="novelty_check",
            tool_description="Runs web search to check idea novelty and find competitors. Returns NoveltyReport JSON including search snippets.",
        ),
        strategy_agent.as_tool(
            tool_name="synthesize_strategy",
            tool_description="Creates the Strategy Note JSON from idea, requirements, and novelty report.",
        ),
        outline_agent.as_tool(
            tool_name="make_outline",
            tool_description="Builds the section outline JSON using required sections and word caps.",
        ),
        draft_agent.as_tool(
            tool_name="draft_sections",
            tool_description="Writes a single SectionDraft JSON.",
        ),
        # All review/guardrail agents removed
    ],
)


# -----------------------------
# CLI & run loop
# -----------------------------

def build_user_prompt(idea_text: str, grant_file: str, out_dir: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"NOW: {now}\n"
        f"GRANT_FILE_PATH: {grant_file}\n"
        f"OUTPUT_DIR: {out_dir}\n"
        "USER_IDEA:\n"
        f"{idea_text.strip()}\n\n"  # This 'idea_text' is the raw, un-redacted version
        "Proceed with the orchestrated execution plan."
    )


def main():
    parser = argparse.ArgumentParser(description="Grant writer via OpenAI Agents SDK (Simplified)")
    parser.add_argument("--grant-file", required=True, help="Path to grant description .txt")
    parser.add_argument("--idea-file", required=True, help="Path to project idea .txt")
    parser.add_argument("--out", default="./submission_kit", help="Output folder")
    args = parser.parse_args()

    try:
        idea_path = Path(args.idea_file)
        if not idea_path.exists():
            raise FileNotFoundError(f"Idea file not found: {args.idea_file}")
        if idea_path.suffix.lower() != ".txt":
            raise ValueError("Idea file must be a .txt")

        idea_text = idea_path.read_text(encoding="utf-8")
        if not idea_text.strip():
            print(f"Idea file is empty: {args.idea_file}. Exiting.")
            return
    except Exception as e:
        print(f"Error reading idea file: {e}")
        sys.exit(1)

    # PII redaction call removed

    # Kick off the orchestrator
    input_blob = build_user_prompt(idea_text, args.grant_file, args.out)

    # Be robust to SDK variations in Runner/Result shapes
    run_fn = getattr(Runner, "run_sync", None) or getattr(Runner, "run", None)
    if run_fn is None:
        raise RuntimeError("Agents SDK Runner has no run/run_sync method in this version.")

    print(f"\n🚀 Kicking off grant writing process for '{args.idea_file}'... This may take several minutes.\n")

    try:
        result = run_fn(orchestrator, input_blob)

        # Try common output properties
        text = getattr(result, "final_output", None)
        if not text:
            text = getattr(result, "output_text", None)
        if not text and hasattr(result, "messages"):
            msgs = result.messages
            if msgs:
                agent_messages = [m.content for m in msgs if m.role == 'agent' and m.content]
                if agent_messages:
                    text = agent_messages[-1]
                else:
                    text = str(msgs[-1])  # Fallback

        print("\n=== DONE ===\n")
        print(text or "Run completed.")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"The process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()