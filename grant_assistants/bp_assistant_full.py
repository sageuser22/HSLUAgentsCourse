# bp_assistant_full.py
# OpenAI Agents SDK orchestration for grant writing
# Inputs: user idea from --idea-file .txt, grant description from --grant-file .txt
# Outputs: submission kit folder with strategy note, outline, draft narrative, rubric score, compliance report

import argparse
import json
import os
import re  # --- MODIFICATION: Added for PII Redaction
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# --- MODIFICATION ---
# Added the OpenAI client, as it's required for the Moderation API guardrail.
from openai import OpenAI

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

# --- MODIFICATION ---
# Instantiate the client now that the API key is loaded.
# This client will be used by the 'read_local_file' moderation guardrail.
try:
    client = OpenAI()
except Exception as e:
    print(f"CRITICAL: Failed to instantiate OpenAI client. {e}")
    sys.exit(1)

# OpenAI Agents SDK
# --- MODIFICATION ---
# Added WebSearchTool and ModelSettings
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
    rubric: List[Dict[str, Any]] = []
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

# --- MODIFICATION: Added new model for a 'RubricScore' edit item ---
class RubricEditItem(BaseModel):
    location: str
    change: str
    gain: float # Using float for a score gain

class RubricScore(BaseModel):
    score: float
    # --- MODIFICATION: Replaced List[Dict] with new concrete model ---
    edits: List[RubricEditItem]


class ComplianceItem(BaseModel):
# ... (code unchanged) ...
    suggestion: Optional[str] = None

# --- MODIFICATION: Added new model for a 'SearchSnippet' item ---
class SearchSnippet(BaseModel):
    source: str
    snippet: str
    # You can add 'url: Optional[str] = None' if your search tool provides it

class ComplianceItem(BaseModel):
    item: str
    status: str  # "OK" | "FIX"
    suggestion: Optional[str] = None

# --- MODIFICATION: Added new model for a 'SearchSnippet' item ---
class SearchSnippet(BaseModel):
    source: str
    snippet: str

class NoveltyReport(BaseModel):
    novelty_score: int  # Score from 0 (not novel) to 100 (highly novel)
    key_competitors: List[str] = []
    key_differentiators: List[str] = []
    summary: str = "Brief rationale for the score and findings."
    # --- MODIFICATION: Replaced List[Dict] with new concrete model ---
    search_snippets: List[SearchSnippet] = []


# --- MODIFICATION: New data shape for Bias/Inclusivity Guardrail ---
class InclusivityItem(BaseModel):
    location_text: str
    issue: str  # e.g., "Gendered language", "Biased assumption"
    suggestion: str


class InclusivityReport(BaseModel):
    status: str  # "OK" | "FIX_NEEDED"
    items: List[InclusivityItem] = []
    summary: str = "Overall assessment of inclusivity."


# --- MODIFICATION: New data shape for Factual Grounding Guardrail ---
class FactCheckItem(BaseModel):
    claim_text: str
    status: str  # "VERIFIED" | "UNVERIFIED" | "INACCURATE"
    evidence: Optional[str] = None
    suggestion: str = ""


class FactCheckReport(BaseModel):
    status: str  # "OK" | "FIX_NEEDED"
    items: List[FactCheckItem] = []
    summary: str = "Overall assessment of factual grounding."


# -----------------------------
# Deterministic tools the agent can call
# -----------------------------

# --- MODIFICATION ---
# Added two critical guardrails to the file reading tool.
@function_tool
def read_local_file(path: str) -> str:
    """
    Read a local UTF-8 text file and return its contents. Must be .txt.
    This tool includes guardrails for file size and content moderation.
    """
    # Set a reasonable max file size for a text-based grant document (e.g., 5MB)
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

    p = Path(path)

    # --- Guardrail 1: Technical File Checks (Size, Existence, Type) ---
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Grant file not found: {path}")

    if p.suffix.lower() != ".txt":
        raise ValueError("Grant file must be a .txt")

    file_size = p.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File size ({file_size} bytes) exceeds the {MAX_FILE_SIZE_BYTES} byte limit. "
            "Please provide a smaller document."
        )
    if file_size < 100:  # A reasonable minimum for a real grant call
        raise ValueError(
            f"File content is too short ({file_size} bytes). "
            "Please provide a valid grant document."
        )

    # --- Read file ---
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")

    # --- Guardrail 2: OpenAI Content Moderation ---
    # This checks the *content* of the grant file for safety.
    try:
        mod_response = client.moderations.create(input=content)

        if mod_response.results[0].flagged:
            # Find out what categories were flagged
            flagged_categories = [
                cat for cat, flagged in mod_response.results[0].categories.model_dump().items() if flagged
            ]
            raise ValueError(
                f"Input file content was flagged by OpenAI's moderation policy for: "
                f"{', '.join(flagged_categories)}. Aborting process for safety."
            )
    except Exception as e:
        # Catch potential API errors during moderation
        raise RuntimeError(f"Failed to run content moderation guardrail: {e}")

    # If all guardrails pass, return the content
    return content


@function_tool
def word_count(text: str) -> int:
    """Return the word count for a given string."""
    return len([w for w in text.split() if w.strip()])


@function_tool
def merge_sections_to_markdown(section_drafts: List[SectionDraft]) -> str:
    """Deterministically merge SectionDrafts (list of dicts) into a single Markdown narrative."""
    parts = []
    for sd in section_drafts:
        # Now that the input is cast to SectionDraft, this 'if' block will always be used
        if isinstance(sd, BaseModel):
            title = (sd.headline or sd.section or "Section").strip()
            body = (sd.body or "").strip()
        else:
            # This 'else' block is now redundant but harmless
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
        rubric_scorecard: RubricScore,
        compliance_checklist: List[ComplianceItem],
) -> str:
    """Write files to a folder so the user can submit easily."""

    def _to_str(x):
        if isinstance(x, BaseModel):
            return x.model_dump_json(indent=2)
        # Handle lists of BaseModels (like compliance_checklist)
        if isinstance(x, list) and x and isinstance(x[0], BaseModel):
            return json.dumps([item.model_dump() for item in x], ensure_ascii=False, indent=2)
        # Handle plain dicts/lists (though Pydantic models are preferred)
        if isinstance(x, (dict, list)):
            return json.dumps(x, ensure_ascii=False, indent=2)
        # Handle strings (like narrative_md)
        return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, indent=2)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # --- MODIFICATION: Now just writing the variables directly ---
    (out / "strategy_note.json").write_text(_to_str(strategy_note), encoding="utf-8")
    (out / "outline.json").write_text(_to_str(outline), encoding="utf-8")
    (out / "novelty_report.json").write_text(_to_str(novelty_report), encoding="utf-8")
    (out / "narrative.md").write_text(_to_str(narrative_md), encoding="utf-8")
    (out / "rubric_scorecard.json").write_text(_to_str(rubric_scorecard), encoding="utf-8")
    (out / "compliance_checklist.json").write_text(_to_str(compliance_checklist), encoding="utf-8")
    return f"Wrote files to {str(out.resolve())}"


# -----------------------------
# Specialized agents
# -----------------------------

MODEL = "gpt-5"

requirements_agent = Agent(
    name="requirements_agent",
    model=MODEL,
    instructions=(
        "You extract a structured requirement summary from a grant call. "
        "Return a complete JSON using the GrantRequirements schema: "
        "{name,funder,deadline_utc,currency,min_amount,max_amount,eligibility_summary,"
        "prohibited,required_sections,word_limits,rubric,attachments}. "
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
        "You MUST adhere to the 'target_words' limit. "
        "After writing your draft, YOU MUST call `word_count` on the 'body' text to check your work. "
        "If the count exceeds 'target_words', you MUST revise your text to be at or below the limit. "
        "Only return the final, compliant SectionDraft. Prefer active voice; avoid ungrounded claims."
    ),
    tools=[word_count],
)

scorer_agent = Agent(
    name="scorer_agent",
    model=MODEL,
    instructions=(
        "You are a rubric critic. Score a given narrative against the rubric (0-100). "
        "Return RubricScore JSON with 3-5 high-leverage, concrete edits and estimated gains."
    ),
)

compliance_agent = Agent(
    name="compliance_agent",
    model=MODEL,
    instructions=(
        "You are a compliance checker. Given the draft by sections (a list of SectionDraft dicts), "
        "the word_limits, required_sections, and attachments, return a list of ComplianceItem JSON records. "
        "Flag missing sections, word limit overages, or missing attachments."
    ),
)

fit_gate_agent = Agent(
    name="fit_gate_agent",
    model=MODEL,
    instructions=(
        "You are a fast eligibility/fit checker. Given the requirements and the user's idea, "
        "return JSON: { 'eligible': true|false, 'fit_score': int(0-100), 'rationale': '...'} . "
        "If ineligible, explain the blocking rule (e.g., entity type, geography, prohibited activities)."
    ),
)

# --- MODIFICATION ---
# Updated novelty_agent to use WebSearchTool and return snippets for fact-checking.
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

# --- MODIFICATION ---
# Added new guardrail agents: 'inclusivity_agent' and 'fact_check_agent'.

inclusivity_agent = Agent(
    name="inclusivity_agent",
    model=MODEL,
    instructions=(
        "You are an expert in DEIB (Diversity, Equity, Inclusion, and Belonging). "
        "Review the provided narrative text. Identify any language that is non-inclusive, "
        "biased, uses stereotypes, or is not people-first. "
        "Return an `InclusivityReport` JSON. If no issues are found, return "
        "`{'status': 'OK', 'items': [], 'summary': 'No inclusivity issues found.'}`. "
        "If issues are found, return `{'status': 'FIX_NEEDED', 'items': [...], 'summary': '...'}`, "
        "where each item provides a concrete suggestion."
    ),
)

fact_check_agent = Agent(
    name="fact_check_agent",
    model=MODEL,
    instructions=(
        "You are a meticulous fact-checker. You will receive a narrative text and "
        "a list of `search_snippets` (the evidence). "
        "1. Extract all quantifiable claims (percentages, statistics, dollar amounts, data points) from the narrative. "
        "2. For each claim, try to verify it against the provided `search_snippets`. "
        "3. Return a `FactCheckReport` JSON. For each claim, create an item. "
        "   - Set status to 'VERIFIED' if supported by a snippet (include snippet in 'evidence'). "
        "   - Set status to 'UNVERIFIED' if not mentioned in any snippet. "
        "   - Set status to 'INACCURATE' if contradicted by a snippet. "
        "If no verifiable claims are made, return `{'status': 'OK', 'items': [], 'summary': 'No verifiable claims found.'}`."
    ),
)

# --- MODIFICATION ---
# Updated refine_agent instructions to accept and integrate feedback from the new guardrails.
refine_agent = Agent(
    name="refine_agent",
    model=MODEL,
    instructions=(
        "You are a master editor. You will receive a list of section drafts (`List[SectionDraft]`) "
        "and three critique reports: "
        "1. `rubric_scorecard`: High-level quality and rubric edits. "
        "2. `inclusivity_report`: Fixes for biased or non-inclusive language. "
        "3. `fact_check_report`: Fixes for unverified or inaccurate claims. "
        "Your task is to integrate the *intent* of all reports to improve the drafts. "
        "Prioritize fixing `inclusivity` and `fact_check` issues. "
        "Apply `rubric` feedback to enhance clarity and impact. "
        "You MUST return an updated **list of `SectionDraft` JSON objects** "
        "(schema: [{section, headline, body}]), NOT a single merged string."
    ),
)

# -----------------------------
# Orchestrator agent (calls the specialists & tools)
# -----------------------------

# --- MODIFICATION ---
# Updated the orchestrator's instructions for Phase 3 and 4 to implement
# an iterative refinement loop with the new guardrails.
orchestrator = Agent(
    name="orchestrator",
    model=MODEL,
    instructions=(
        "You are the grant writing coordinator. You MUST follow this execution plan strictly. "
        "Inputs are provided in the message content: NOW, GRANT_FILE_PATH, OUTPUT_DIR, and USER_IDEA.\n\n"

        "--- PHASE 1: INTAKE & VALIDATION (Sequential) ---\n"
        "1) Call `read_local_file(GRANT_FILE_PATH)` to load the grant call text. "
        "   This function contains guardrails; if it fails, the process will stop. Log the error and halt.\n"
        "2) Call `extract_requirements` with the grant call text to get `GrantRequirements` JSON.\n"
        "3) Call `fit_gate` with (requirements, user idea) to get eligibility.\n"
        "4) **[GATE]** Check the result from `fit_gate`. If 'eligible' is false or 'fit_score' < 50, "
        "   STOP the process. Print a clear message to the user explaining the ineligibility/low fit "
        "   and do not proceed to Phase 2. Otherwise, continue.\n\n"

        "--- PHASE 2: STRATEGY & DRAFTING (Parallel) ---\n"
        "5) Call `novelty_check` (user idea, requirements) to get the `NoveltyReport` JSON. "
        "   This report (variable `novelty_report`) contains the `search_snippets` needed for Phase 3.\n"
        "6) **[Parallel Task]** These two tasks can run in parallel. Wait for both to complete:\n"
        "   a) Call `synthesize_strategy` (idea, requirements, novelty_report) -> `StrategyNote` (variable `strategy_note`)\n"
        "   b) Call `make_outline` (requirements, idea) -> `Outline` (variable `outline`)\n"
        "7) **[Parallel Task]** For EACH item in the `Outline`, call `draft_sections` in parallel "
        "   to get a list of `SectionDraft` JSONs. Wait for ALL drafts to be returned. "
        "   SET this list as `current_draft_list`.\n\n"

        "--- PHASE 3: REVIEW & REFINEMENT LOOP (Iterative) ---\n"
        "8)  SET MAX_ATTEMPTS = 3. SET ATTEMPT = 1.\n"
        "9)  **[Refinement Loop Start]**\n"
        "10) Call `merge_sections_to_markdown` (`current_draft_list`) -> `current_narrative`.\n"
        "11) **[Parallel Review]** Run all three review agents in parallel. Wait for all to complete:\n"
        "    a) Call `score_rubric` (`current_narrative`, requirements.rubric) -> `current_scorecard`.\n"
        "    b) Call `check_inclusivity` (`current_narrative`) -> `inclusivity_report`.\n"
        "    c) Call `check_facts` (`current_narrative`, `novelty_report.search_snippets`) -> `fact_check_report`.\n"
        "12) **[GATE]** Check `current_scorecard` and reports. If (`current_scorecard.score` >= 90 "
        "     AND `inclusivity_report.status` == 'OK' AND `fact_check_report.status` == 'OK') "
        "     OR ATTEMPT >= MAX_ATTEMPTS: \n"
        "     - SET `narrative_final` = `current_narrative`\n"
        "     - SET `rubric_scorecard_final` = `current_scorecard`\n"
        "     - SET `draft_list_final` = `current_draft_list`\n"
        "     - Print a message that the refinement loop is complete (e.g., 'Refinement loop finished on attempt {ATTEMPT} with score {score}').\n"
        "     - BREAK the loop and proceed to Phase 4.\n"
        "13) **[Refinement]** Call `refine_draft` with (`current_draft_list`, `current_scorecard`, `inclusivity_report`, `fact_check_report`) "
        "     to get an improved list of drafts.\n"
        "     - SET `current_draft_list` = the new list of `SectionDraft` objects returned from `refine_draft`.\n"
        "14) INCREMENT ATTEMPT.\n"
        "15) Go to step 10.\n\n"

        "--- PHASE 4: FINAL PACKAGING (Sequential) ---\n"
        "16) **[Final Checks]** Run the final compliance check on the loop's output.\n"
        "    - Call `check_compliance` (`draft_list_final`, requirements) -> `compliance_checklist_final`.\n"

        # --- MODIFICATION: Updated Step 17 to use new named arguments ---
        "17) Call `save_submission_kit`(out_dir=OUTPUT_DIR, strategy_note=strategy_note, outline=outline, "
        "     novelty_report=novelty_report, narrative_md=narrative_final, "
        "     rubric_scorecard=rubric_scorecard_final, compliance_checklist=compliance_checklist_final).\n"

        "18) Finally, print a short human-readable summary of the process and the output folder path."
    ),
    tools=[
        read_local_file,
        word_count,
        # ... (rest of the file is unchanged) ...
        merge_sections_to_markdown,
        save_submission_kit,
        requirements_agent.as_tool(
            tool_name="extract_requirements",
            tool_description="Extracts and structures the grant call requirements into JSON.",
        ),
        fit_gate_agent.as_tool(
            tool_name="fit_gate",
            tool_description="Quick eligibility/fit gate; returns eligible flag and fit score.",
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
            tool_description="Writes a single SectionDraft JSON that respects target word counts.",
        ),
        scorer_agent.as_tool(
            tool_name="score_rubric",
            tool_description="Scores narrative against rubric and suggests edits, returns JSON.",
        ),
        compliance_agent.as_tool(
            tool_name="check_compliance",
            tool_description="Checks word caps, required sections, and attachments; returns JSON list.",
        ),
        refine_agent.as_tool(
            tool_name="refine_draft",
            tool_description="Applies critique from all reports (rubric, inclusivity, fact-check) to a draft list to create an improved v2 list.",
        ),
        # --- MODIFICATION: Added new guardrail tools ---
        inclusivity_agent.as_tool(
            tool_name="check_inclusivity",
            tool_description="Checks narrative for bias and non-inclusive language. Returns InclusivityReport JSON.",
        ),
        fact_check_agent.as_tool(
            tool_name="check_facts",
            tool_description="Fact-checks narrative claims against provided web snippets. Returns FactCheckReport JSON.",
        ),
    ],
)


# -----------------------------
# --- MODIFICATION: Added PII Guardrail Function ---
# -----------------------------

def redact_pii(text: str) -> str:
    """
    Scrubs common PII from input text using simple regex.
    This is an input guardrail to protect user privacy.
    """
    print("    Scrubbing user idea for PII...")
    # Basic email regex
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", text)
    # Basic phone regex (handles many US/Intl formats)
    text = re.sub(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?[\d\s-]{7,10}", "[REDACTED_PHONE]", text)
    # Basic SSN/Tax ID regex
    text = re.sub(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "[REDACTED_ID_NUMBER]", text)

    return text


# -----------------------------
# CLI & run loop
# -----------------------------

def build_user_prompt(idea_text: str, grant_file: str, out_dir: str) -> str:
    now = datetime.utcnow().strftime("%Y-m-%d %H:%M:%S UTC")
    return (
        f"NOW: {now}\n"
        f"GRANT_FILE_PATH: {grant_file}\n"
        f"OUTPUT_DIR: {out_dir}\n"
        "USER_IDEA:\n"
        f"{idea_text.strip()}\n\n"  # This 'idea_text' is now the scrubbed version
        "Proceed with the orchestrated execution plan."
    )


def main():
    parser = argparse.ArgumentParser(description="Grant writer via OpenAI Agents SDK")
    parser.add_argument("--grant-file", required=True, help="Path to grant description .txt")
    # --- MODIFICATION: Added --idea-file argument ---
    parser.add_argument("--idea-file", required=True, help="Path to project idea .txt")
    parser.add_argument("--out", default="./submission_kit", help="Output folder")
    args = parser.parse_args()

    # --- MODIFICATION: Removed stdin reading, now reading from --idea-file ---
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
    # ---

    # --- MODIFICATION: Apply PII Guardrail ---
    # This cleans the text *before* it is passed to the user prompt and agents.
    idea_text_clean = redact_pii(idea_text)
    # ---

    # Kick off the orchestrator
    input_blob = build_user_prompt(idea_text_clean, args.grant_file, args.out)

    # Be robust to SDK variations in Runner/Result shapes
    run_fn = getattr(Runner, "run_sync", None) or getattr(Runner, "run", None)
    if run_fn is None:
        raise RuntimeError("Agents SDK Runner has no run/run_sync method in this version.")

    # --- MODIFICATION: Updated print statement ---
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
        # --- MODIFICATION ---
        # Catch errors from the run, which will now include our guardrail failures.
        print(f"\n--- ERROR ---")
        print(f"The process failed: {e}")
        print(
            "This could be due to a guardrail failure (e.g., file size, content moderation, PII issue) or an agent error.")
        sys.exit(1)


if __name__ == "__main__":
    main()