Here is a complete README file for your project, structured to explain the 4-example progression and built to work with the Poetry setup.

-----

```md
# Grant Writing Assistant: Multi-Agent Coordination Examples

This repository demonstrates how to build a sophisticated, multi-agent system using the OpenAI Agents SDK. The project progressively builds from a single simple agent to a robust, multi-agent orchestrator that automates the grant writing process.

The final example (`bp_assistant_full.py`) takes a project idea and a grant description as input, and produces a complete "submission kit" folder with a draft narrative, strategic analysis, compliance reports, and more.

## 🚀 Core Features (of the final example)

* **Multi-Agent Orchestration**: A central `orchestrator` agent manages a team of specialist agents, each with a specific role (e.g., parsing, drafting, scoring, fact-checking).
* **Iterative Refinement Loop**: The system doesn't just write a draft; it critiques, fact-checks, and refines it in a loop until quality and safety standards are met.
* **Automated Web Research**: A `novelty_agent` uses the `WebSearchTool` to research the competitive landscape and assess the idea's novelty.
* **Robust Guardrails**: Implements multiple layers of safety:
    * **Input Guardrail**: Automatically redacts PII (emails, phone numbers) from the user's idea file.
    * **Tool Guardrail**: Moderates input files for harmful content using the OpenAI Moderation API and checks for file size limits.
    * **Review Guardrails**: Dedicated agents check the draft for inclusivity, bias, and factual accuracy.
* **Parallel Processing**: The architecture is designed for specialist agents (like drafting and review) to be run in parallel, speeding up the process.
* **Structured I/O**: Uses Pydantic models to ensure all data passed between agents is structured, validated, and reliable.

---

## 🏗️ Project Structure

This repository is structured to show a logical progression of agent complexity.

```

.
├── grant\_assistants/
│   ├── **init**.py
│   ├── grant\_fit\_simple\_agent.py   \# Example 1: Single Agent
│   ├── bp\_assistant\_seq.py         \# Example 2: Sequential Agents
│   ├── bp\_assistant\_orc.py         \# Example 3: Orchestrator Pattern
│   ├── bp\_assistant\_full.py        \# Example 4: Full Guard-railed Orchestrator
│   └── ... (other examples)
├── sample-docs/
│   ├── idea.txt                    \# Sample idea file
│   └── grant.txt                   \# Sample grant description
├── .env.example                    \# API Key template
├── LICENSE
├── pyproject.toml                  \# Poetry dependencies
└── README.md

````

---

## 🔧 Installation & Setup (with Poetry)

This project uses [Poetry](https://python-poetry.org/) for dependency and environment management.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Install Poetry:**
    Follow the [official Poetry installation guide](https://python-poetry.org/docs/#installation) if you don't already have it.

3.  **Install Dependencies:**
    Poetry will read the `pyproject.toml` file, create a virtual environment, and install all required packages.
    ```bash
    poetry install
    ```

---

## 🔑 Configuration

The assistant requires an OpenAI API key.

1.  **Create a `.env` file:**
    Copy the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Add your API Key:**
    Edit the `.env` file and add your `OPENAI_API_KEY`:
    ```
    OPENAI_API_KEY="sk-..."
    ```

The scripts will automatically load this key.

---

## 🚀 The 4 Examples: From Simple to Complex

These examples are designed to be run in order, demonstrating how to build a complex multi-agent system.

All commands should be run using `poetry run`, which executes them inside the project's virtual environment.

### Example 1: The Simple Agent

This agent performs a single, specific task with a few tools. It reads two files, reasons about their contents, and saves a JSON report.

* **File:** `grant_assistants/grant_fit_simple_agent.py`
* **Concept:** A single agent with a clear set of instructions and tools (`read_local_file`, `save_fit_report`).
* **To Run:**
    ```bash
    poetry run python grant_assistants/grant_fit_simple_agent.py \
      --idea "sample-docs/idea.txt" \
      --grant "sample-docs/grant.txt" \
      --out "fit_report.json"
    ```

### Example 2: Sequential Workflow

This example introduces a multi-agent workflow, but in a rigid, sequential chain. Agent 1 does its job and then "hands off" control to Agent 2, who hands off to Agent 3.

* **File:** `grant_assistants/bp_assistant_seq.py`
* **Concept:** Using the `handoff()` function to create an "assembly line" of agents. This is useful for simple, linear processes.
* **To Run:**
    ```bash
    poetry run python grant_assistants/bp_assistant_seq.py \
      --grant-file "sample-docs/grant.txt" \
      --idea-file "sample-docs/idea.txt"
    ```

### Example 3: The Orchestrator Pattern

This is the most common and powerful multi-agent pattern. A central "manager" agent (`orchestrator`) coordinates a team of "specialist" agents.

* **File:** `grant_assistants/bp_assistant_orc.py`
* **Concept:** Using the `.as_tool()` method to turn specialist agents (`draft_agent`, `scorer_agent`) into tools that the `orchestrator` can call. This allows for flexible, non-linear workflows.
* **To Run:**
    ```bash
    poetry run python grant_assistants/bp_assistant_orc.py \
      --grant-file "sample-docs/grant.txt" \
      --idea-file "sample-docs/idea.txt" \
      --out "./submission_kit_orc"
    ```

### Example 4: The Full Guard-railed Orchestrator

This is the complete, production-ready version. It expands on the orchestrator pattern by adding:
1.  More specialist agents (Novelty, Fact-Checking, Inclusivity).
2.  Robust input and tool guardrails (PII, Moderation).
3.  An iterative "Critique & Refine" loop.

* **File:** `grant_assistants/bp_assistant_full.py`
* **Concept:** A robust, resilient, and safe multi-agent system that iteratively improves its own output.
* **To Run:**
    ```bash
    poetry run python grant_assistants/bp_assistant_full.py \
      --grant-file "sample-docs/grant.txt" \
      --idea-file "sample-docs/idea.txt" \
      --out "./submission_kit_full"
    ```
* **Output:** This will create a `submission_kit_full` folder containing the complete set of generated documents.

---



## 🌊 Workflow Deep Dive (`bp_assistant_full.py`)

The final agent's logic is broken into four distinct phases:

### Phase 1: Intake & Validation (Sequential)

1.  **PII Guardrail**: The user's idea from `idea.txt` is scrubbed for PII (emails, phones) *before* it's sent to any agent.
2.  **File Guardrail**: The `read_local_file` tool reads `grant.txt`, checking file size and type.
3.  **Moderation Guardrail**: The content of `grant.txt` is sent to the OpenAI Moderation API. If it's flagged, the entire process stops.
4.  **Fit Gate**: The `fit_gate_agent` compares the (clean) idea to the grant. If `eligible` is false or `fit_score` is low, the process stops here to save time and money.

### Phase 2: Strategy & Drafting (Parallel)

1.  **Novelty Check**: The `novelty_agent` uses `WebSearchTool` to find competitors and evidence. This generates a `NoveltyReport` (including search snippets).
2.  **Strategy & Outline**: The `strategy_agent` and `outline_agent` run in parallel to create the high-level plan (`StrategyNote`) and the writing skeleton (`Outline`).
3.  **Drafting**: The `draft_agent` is called in parallel for *each section* in the outline, producing a list of `SectionDraft` objects.

### Phase 3: Review & Refinement Loop (Iterative)

This is the most complex phase. The system loops (up to 3 times) to improve the draft.

1.  **Merge**: The list of drafts is merged into a single `current_narrative` string.
2.  **Parallel Review**: Three specialist agents review the `current_narrative` *in parallel*:
      * `scorer_agent` -\> (Checks quality)
      * `inclusivity_agent` -\> (Checks for bias)
      * `fact_check_agent` -\> (Checks claims against the `NoveltyReport` snippets)
3.  **Gate Check**: The orchestrator checks the reports. If the `score >= 90` AND `inclusivity.status == 'OK'` AND `fact_check.status == 'OK'`, the loop finishes early.
4.  **Refine**: If goals are not met, the `refine_agent` is called. It receives the list of drafts and all three critique reports, and produces a *new, improved list of drafts*.
5.  **Loop**: The new list becomes the `current_draft_list`, and the process repeats.

### Phase 4: Final Packaging (Sequential)

1.  **Final Compliance**: The `compliance_agent` runs one last check on the final draft to check for missing sections or word count violations.
2.  **Save Kit**: The `save_submission_kit` tool writes all final artifacts (strategy, outline, novelty report, final narrative, etc.) to the output directory.

-----

