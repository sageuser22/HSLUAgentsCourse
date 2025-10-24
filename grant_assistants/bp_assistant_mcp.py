# bp_assistant_mcp.py — improved MCP-aligned version

import argparse
import json
import os
import sys
import time
import socket
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import concurrent.futures
from urllib.parse import urlparse

from pydantic import BaseModel, ValidationError

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
from agents import Agent, Runner, WebSearchTool
from agents.model_settings import ModelSettings

# -----------------------------
# Data shapes (Our "Context")
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
    attachments: List[str] = {}
    rubric_weights: Dict[str, int] = {}  # NEW: pass-through to drafting

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
    source: str  # URL or source id
    snippet: str

class NoveltyReport(BaseModel):
    novelty_score: int
    key_competitors: List[str] = []
    key_differentiators: List[str] = []
    summary: str = ""
    search_snippets: List[SearchSnippet] = []

# -----------------------------
# Deterministic I/O & Utility
# -----------------------------
MAX_FILE_BYTES = 500_000  # ~500 KB

def read_local_file(path: str) -> str:
    """
    Read a local UTF-8 text file and return its contents. Must be .txt and <= MAX_FILE_BYTES.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not p.is_file():
        raise ValueError(f"Path is not a file: {path}")
    if p.suffix.lower() != ".txt":
        raise ValueError(f"Unsupported file type '{p.suffix}'. Expected a .txt file: {path}")
    if p.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"File too large ({p.stat().st_size} bytes). Max allowed is {MAX_FILE_BYTES} bytes: {path}")
    try:
        content = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"File is not valid UTF-8 text: {path}")
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")
    return content

def merge_sections_to_markdown(section_drafts: List[SectionDraft]) -> str:
    """Deterministically merge SectionDrafts into a single Markdown narrative."""
    parts = []
    for sd in section_drafts:
        title = (sd.headline or sd.section or "Section").strip()
        body = (sd.body or "").strip()
        parts.append(f"## {title}\n\n{body}")
    return "\n\n".join(parts).strip()

def save_submission_kit(
    out_dir: str,
    strategy_note: StrategyNote,
    outline: Outline,
    novelty_report: NoveltyReport,
    narrative_md: str,
    run_log: Dict[str, Any],
) -> str:

    def _to_str(x):
        if isinstance(x, BaseModel):
            return x.model_dump_json(indent=2)
        return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, indent=2)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "strategy_note.json").write_text(_to_str(strategy_note), encoding="utf-8")
    (out / "outline.json").write_text(_to_str(outline), encoding="utf-8")
    (out / "novelty_report.json").write_text(_to_str(novelty_report), encoding="utf-8")
    (out / "narrative.md").write_text(_to_str(narrative_md), encoding="utf-8")
    (out / "run_log.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")

    return f"Wrote files to {str(out.resolve())}"

def _cap_words(text: str, cap: int) -> str:
    if cap <= 0:
        return text
    words = text.split()
    if len(words) <= cap:
        return text
    return " ".join(words[:cap])

def _hostname(u: str) -> str:
    try:
        return urlparse(u).hostname or u
    except Exception:
        return u

# -----------------------------
# Agent factory helpers
# -----------------------------
MODEL = "gpt-5"  # your target model

def json_response_format_for(model: BaseModel) -> Dict[str, Any]:
    # If your SDK supports JSON schema response_format, wire it here.
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model.__class__.__name__ if isinstance(model, BaseModel) else str(model),
            "schema": model.model_json_schema()
        }
    }

COMMON_SETTINGS = dict(
    top_p=1.0,
    seed=7,
    max_output_tokens=1500,
)

requirements_agent = Agent(
    name="requirements_agent",
    model=MODEL,
    instructions=(
        "Extract grant requirements and return exactly the GrantRequirements JSON. "
        "Include required_sections and word_limits if present; infer rubric_weights if provided."
    ),
    model_settings=ModelSettings(
        response_format={"type": "json_schema", "json_schema": {"name": "GrantRequirements", "schema": GrantRequirements.model_json_schema()}},
        **COMMON_SETTINGS
    ),
)

strategy_agent = Agent(
    name="strategy_agent",
    model=MODEL,
    instructions=(
        "You are a senior grant strategist. Given the applicant's idea, grant requirements, "
        "and a NoveltyReport, write a concise StrategyNote JSON. "
        "Emphasize differentiators and value-for-money. Be specific and brief."
    ),
    model_settings=ModelSettings(
        response_format={"type": "json_schema", "json_schema": {"name": "StrategyNote", "schema": StrategyNote.model_json_schema()}},
        **COMMON_SETTINGS
    ),
)

outline_agent = Agent(
    name="outline_agent",
    model=MODEL,
    instructions=(
        "Create a section-by-section outline as Outline JSON. "
        "Ensure every 'required_sections' from the grant is included. "
        "Set 'target_words' to respect word_limits if provided. "
        "Bias content toward rubric_weights (relevance, impact, feasibility, capacity, measurement)."
    ),
    model_settings=ModelSettings(
        response_format={"type": "json_schema", "json_schema": {"name": "Outline", "schema": Outline.model_json_schema()}},
        **COMMON_SETTINGS
    ),
)

draft_agent = Agent(
    name="draft_agent",
    model=MODEL,
    instructions=(
        "You are a grant writer. Given one OutlineItem, return a SectionDraft JSON. "
        "Adhere to 'target_words' and reflect key_messages. "
        "Make content concrete, evidence-oriented, and aligned with rubric_weights (if provided)."
    ),
    model_settings=ModelSettings(
        response_format={"type": "json_schema", "json_schema": {"name": "SectionDraft", "schema": SectionDraft.model_json_schema()}},
        **COMMON_SETTINGS
    ),
)

novelty_agent = Agent(
    name="novelty_agent",
    model=MODEL,
    instructions=(
        "Market & research analyst role. Steps:\n"
        "1) Generate 2–3 competitor/differentiator search queries.\n"
        "2) Call WebSearchTool for each.\n"
        "3) Deduplicate sources by hostname, keep the most relevant per host.\n"
        "4) Return NoveltyReport JSON with key_competitors, key_differentiators, novelty_score (0-100), "
        "summary (<=120 words), and search_snippets including canonical source URLs."
    ),
    tools=[WebSearchTool()],
    model_settings=ModelSettings(
        tool_choice="auto",
        response_format={"type": "json_schema", "json_schema": {"name": "NoveltyReport", "schema": NoveltyReport.model_json_schema()}},
        **COMMON_SETTINGS
    ),
)

# -----------------------------
# MCP Orchestration (in Python) with retries/telemetry
# -----------------------------
def run_agent(agent: Agent, prompt: str, log: Optional[Dict[str, Any]] = None) -> str:
    """Run an agent with simple retries/backoff and light telemetry."""
    run_fn = getattr(Runner, "run_sync", None) or getattr(Runner, "run", None)
    if run_fn is None:
        raise RuntimeError("Agents SDK Runner has no run/run_sync method.")

    attempts = 0
    delay = 1.0
    last_err: Optional[Exception] = None
    while attempts < 5:
        attempts += 1
        start = time.time()
        try:
            result = run_fn(agent, prompt)
            duration = round(time.time() - start, 3)
            text = getattr(result, "final_output", None) or getattr(result, "text", None)
            if not text and hasattr(result, "messages"):
                msgs = [m.content for m in result.messages if getattr(m, "role", "") == "agent" and m.content]
                text = msgs[-1] if msgs else None
            if not text or not text.strip():
                raise RuntimeError(f"{agent.name} returned empty output")

            if log is not None:
                log_entry = {
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "agent": agent.name,
                    "model": getattr(agent, "model", None),
                    "duration_s": duration,
                    "attempt": attempts,
                    "prompt_chars": len(prompt),
                    "output_chars": len(text),
                }
                log.setdefault("agent_runs", []).append(log_entry)
            return text
        except Exception as e:
            last_err = e
            if log is not None:
                log.setdefault("errors", []).append({
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "agent": agent.name,
                    "attempt": attempts,
                    "error": str(e)
                })
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
    raise RuntimeError(f"Agent {agent.name} failed after {attempts} attempts: {last_err}")

def run_drafting_task(item: OutlineItem, rubric_weights: Optional[Dict[str, int]], run_log: Dict[str, Any]) -> SectionDraft:
    """Wrapper for running the draft_agent in a thread pool with rubric-aware context."""
    print(f"  ...Drafting section: {item.section}")
    # Include rubric weights to steer generation
    payload = {
        "outline_item": item.model_dump(),
        "rubric_weights": rubric_weights or {}
    }
    prompt = f"Draft the following section as SectionDraft JSON.\n{json.dumps(payload, indent=2)}"
    output_json = run_agent(draft_agent, prompt, log=run_log)
    try:
        return SectionDraft.model_validate_json(output_json)
    except ValidationError as ve:
        raise ValueError(f"Invalid SectionDraft JSON for '{item.section}': {ve}") from ve

def _dedup_novelty(nr: NoveltyReport) -> NoveltyReport:
    """De-duplicate search snippets by hostname, keep first occurrence."""
    seen: set = set()
    dedup_snips: List[SearchSnippet] = []
    for s in nr.search_snippets:
        host = _hostname(s.source)
        if host in seen:
            continue
        seen.add(host)
        dedup_snips.append(s)
    nr.search_snippets = dedup_snips
    # Optional: cap to top 8 snippets
    nr.search_snippets = nr.search_snippets[:8]
    return nr

def main():
    parser = argparse.ArgumentParser(description="Grant writer via OpenAI Agents (MCP Pattern)")
    parser.add_argument("--grant-file", required=True, help="Path to grant description .txt")
    parser.add_argument("--idea-file", required=True, help="Path to project idea .txt")
    parser.add_argument("--out", default="./submission_kit", help="Output folder")
    args = parser.parse_args()

    print(f"\n🚀 Kicking off grant writing process (MCP) for '{args.idea_file}'...\n")
    run_log: Dict[str, Any] = {"started": datetime.utcnow().isoformat() + "Z", "agent_runs": [], "errors": []}

    try:
        # --- 1. CONTEXT: Initialization ---
        idea_text = read_local_file(args.idea_file)
        grant_text = read_local_file(args.grant_file)
        out_dir = args.out
        run_log["inputs"] = {"idea_file": args.idea_file, "grant_file": args.grant_file}

        # --- 2. CONTEXT: Requirements ---
        print("1. Extracting requirements...")
        req_prompt = (
            "Here is the grant text. Extract GrantRequirements JSON precisely.\n\n"
            f"{grant_text}"
        )
        requirements_json = run_agent(requirements_agent, req_prompt, log=run_log)
        requirements = GrantRequirements.model_validate_json(requirements_json)
        print(f"   ✅ Done. Found {len(requirements.required_sections)} required sections.")

        # --- 3. CONTEXT: Parallel Strategy Prep ---
        print("2. Running parallel tasks (Novelty & Outline)...")
        novelty_prompt = (
            "User Idea:\n" + idea_text + "\n\n"
            "Grant Context (eligibility summary):\n" + (requirements.eligibility_summary or "")
        )
        outline_prompt = (
            "Create an Outline JSON that fully covers the grant's required sections and respects word limits.\n"
            "Bias toward rubric weights: relevance (25), impact (25), feasibility (20), capacity (15), measurement (15) if present.\n\n"
            f"User Idea:\n{idea_text}\n\n"
            f"Grant Requirements JSON:\n{requirements.model_dump_json(indent=2)}"
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            fut_novelty = executor.submit(run_agent, novelty_agent, novelty_prompt, 120, run_log)
            fut_outline = executor.submit(run_agent, outline_agent, outline_prompt, 120, run_log)

            novelty_report = NoveltyReport.model_validate_json(fut_novelty.result())
            novelty_report = _dedup_novelty(novelty_report)
            print("   ✅ Novelty check complete.")
            outline = Outline.model_validate_json(fut_outline.result())
            print(f"   ✅ Outline complete ({len(outline.items)} sections).")

        # --- 4. CONTEXT: Strategy Synthesis (depends on novelty) ---
        print("3. Synthesizing strategy...")
        strategy_prompt = (
            "Write a concise StrategyNote JSON optimizing for value-for-money and differentiation.\n\n"
            f"User Idea:\n{idea_text}\n\n"
            f"Grant Requirements:\n{requirements.model_dump_json(indent=2)}\n\n"
            f"Novelty Report:\n{novelty_report.model_dump_json(indent=2)}"
        )
        strategy_note_json = run_agent(strategy_agent, strategy_prompt, log=run_log)
        strategy_note = StrategyNote.model_validate_json(strategy_note_json)
        print("   ✅ Strategy complete.")

        # --- 5. CONTEXT: Parallel Drafting (depends on outline) ---
        print(f"4. Drafting {len(outline.items)} sections in parallel...")
        # Preserve order by index, and use adaptive workers to be rate-limit friendly
        ordered_items: List[Tuple[int, OutlineItem]] = list(enumerate(outline.items))
        max_workers = max(1, min(3, len(ordered_items)))  # cap at 3 concurrent calls
        section_drafts_ordered: List[Optional[SectionDraft]] = [None] * len(ordered_items)

        rubric_weights = requirements.rubric_weights if isinstance(requirements.rubric_weights, dict) else {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_drafting_task, item, rubric_weights, run_log): idx
                for idx, item in ordered_items
            }
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                section_drafts_ordered[idx] = future.result()

        section_drafts: List[SectionDraft] = [sd for sd in section_drafts_ordered if sd is not None]
        print("   ✅ All sections drafted (order preserved).")

        # --- 5b. Enforce word caps (grant-level + per-outline item) ---
        limits = requirements.word_limits or {}
        for item, sd in zip(outline.items, section_drafts):
            # Priority: OutlineItem.target_words, else grant-level word_limits by section name/headline
            cap = item.target_words or limits.get(sd.section) or limits.get(sd.headline) or 0
            sd.body = _cap_words(sd.body, cap) if cap else sd.body

        # --- 6. CONTEXT: Final Merge (depends on drafts) ---
        print("5. Merging drafts...")
        final_narrative = merge_sections_to_markdown(section_drafts)
        print(f"   ✅ Narrative merged (~{len(final_narrative.split())} words).")

        # --- 7. I/O: Save Final Artifacts + run log ---
        print("6. Saving submission kit...")
        run_log["finished"] = datetime.utcnow().isoformat() + "Z"
        save_path = save_submission_kit(
            out_dir=out_dir,
            strategy_note=strategy_note,
            outline=outline,
            novelty_report=novelty_report,
            narrative_md=final_narrative,
            run_log=run_log,
        )
        print(f"   ✅ Success! {save_path}")
        print("\n=== DONE ===\n")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"The process failed: {e}")
        import traceback
        traceback.print_exc()
        run_log.setdefault("errors", []).append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "stage": "exception",
            "error": str(e)
        })
        try:
            out_dir = Path(args.out or "./submission_kit")
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "run_log.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
