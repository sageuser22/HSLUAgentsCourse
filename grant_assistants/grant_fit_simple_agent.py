# simple_fit_agent_sdk.py
# Minimal OpenAI Agents SDK example:
# Tools: read_txt (read local .txt), write_json (save result)
# One agent: evaluates grant fit and writes JSON

import argparse
import json
import os, sys
from pathlib import Path

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
from agents import Agent, Runner, function_tool


# -------------------------
# Tools
# -------------------------

@function_tool
def read_txt(path: str) -> str:
    """Read a local UTF-8 .txt file and return its contents."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if p.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file: {path}")
    return p.read_text(encoding="utf-8").strip()

@function_tool
def write_json(path: str, obj_json: str) -> str:
    """Write JSON (given as a string) to the path (creates parent dirs)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    obj = json.loads(obj_json)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Saved fit result to {str(p.resolve())}"


# -------------------------
# Agent
# -------------------------

fit_agent = Agent(
    name="fit_agent",
    model=MODEL,
    instructions=(
        """Role: Professional grant application assessor.
        Inputs: PROJECT_IDEA_FILE, GRANT_REQUIREMENTS_FILE, OUTPUT_JSON_FILE.
           Steps (ReAct):
           1. Act: Call read_local_file(PROJECT_IDEA_FILE) to get the project text.
           2. Act: Call read_local_file(GRANT_REQUIREMENTS_FILE) to get the grant text.
           3. Reason: Compare goals, activities, and outcomes against eligibility, funding priorities, and prohibited activities.
           4. Reason → Decision: Generate a JSON object containing the fit analysis:
              {
                  "is_good_fit": (bool),
                  "fit_score": (int 0–100),
                  "rationale": (string),
                  "key_strengths": [list of strings],
                  "key_weaknesses": [list of strings]
              }
            
           5. Act: Call write_json(path=OUT_JSON, obj_json=<that JSON string>).
           6. Act: Print a short summary, e.g. "Strong fit. Report saved."
           """
    ),
    tools=[read_txt, write_json],
)


# -------------------------
# CLI
# -------------------------

def build_user_message(idea_path: str, grant_path: str, out_json: str) -> str:
    return (
        f"IDEA_FILE_PATH: {idea_path}\n"
        f"GRANT_FILE_PATH: {grant_path}\n"
        f"OUT_JSON: {out_json}\n"
        "Proceed with the steps."
    )

def main():
    parser = argparse.ArgumentParser(description="Simple grant fit agent (OpenAI Agents SDK)")
    parser.add_argument("--idea-file", required=True, help="Path to project idea .txt")
    parser.add_argument("--grant-file", required=True, help="Path to grant requirements .txt")
    parser.add_argument("--out", default="./fit_result.json", help="Output JSON file")
    args = parser.parse_args()

    # Run the agent once; it will call the tools itself
    msg = build_user_message(args.idea_file, args.grant_file, args.out)

    run_fn = getattr(Runner, "run_sync", None) or getattr(Runner, "run", None)
    if not run_fn:
        raise RuntimeError("Agents SDK Runner has no run/run_sync method.")

    print(f"\n🚀 Evaluating fit...\nModel: {MODEL}\nIdea: {args.idea_file}\nGrant: {args.grant_file}\nOut: {args.out}\n")
    result = run_fn(fit_agent, msg)

    # Console-friendly summary (SDK return shapes vary)
    text = getattr(result, "final_output", None) or getattr(result, "output_text", None)
    if not text and hasattr(result, "messages"):
        msgs = result.messages
        if msgs:
            last = msgs[-1]
            text = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else None)

    print("\n=== DONE ===\n")
    print(text or "Run completed. (Fit result saved to JSON)")

if __name__ == "__main__":
    main()
