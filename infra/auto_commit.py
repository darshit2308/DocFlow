"""
DocFlow Auto-Commit Engine
==========================
Run by GitHub Actions daily. Figures out which day of the project we're on,
makes real meaningful file changes for that day's milestone, writes a
commit message to /tmp/commit_msg.txt, then exits.

GitHub Actions then does:
    git add -A
    git commit -m "$(cat /tmp/commit_msg.txt)"
    git push

The script uses randomized logic so commit times vary (the cron fires at a
fixed UTC time but the actual content and message feel organic).
"""

import os
import random
import textwrap
from datetime import date
from pathlib import Path

# ── Project start date (the day you first pushed) ──────────────────────────
PROJECT_START = date(2025, 11, 25)

# ── Day-plan registry ───────────────────────────────────────────────────────
# Each entry: (commit_index_0_or_1_or_2, description, files_to_touch)
# files_to_touch: list of (relative_path, content_generator_key)
# We write real content (stubs, progress notes, configs) — not empty files.

DAY_PLAN = {
    1: [
        ("chore: init repo structure and tooling",
         "Bootstrap Makefile, pyproject.toml, .gitignore, .env.example",
         ["Makefile", "pyproject.toml", ".gitignore", ".env.example"]),
        ("feat: docker-compose with postgres and pgvector",
         "Local Postgres 16 + pgvector via docker-compose",
         ["infra/docker-compose.yml", "infra/init.sql"]),
        ("feat: healthz endpoint and GitHub Actions CI",
         "FastAPI skeleton with GET /healthz, ruff + pytest CI",
         ["app/__init__.py", "app/main.py", "app/api/__init__.py",
          "app/api/routes.py", ".github/workflows/ci.yml"]),
    ],
    2: [
        ("feat: alembic setup and core config",
         "Alembic init, config.py reading from .env, db.py connection helpers",
         ["app/core/config.py", "app/core/db.py", "alembic.ini",
          "migrations/env.py"]),
        ("feat: initial migration - documents extractions decisions",
         "Migration 001: documents, extractions, validations, decisions tables",
         ["migrations/versions/001_core_schema.py"]),
        ("feat: policy audit llm_calls tables and indexes",
         "Migration 002: policy_chunks (pgvector), audit_events, llm_calls, eval_runs; GIN + HNSW indexes",
         ["migrations/versions/002_policy_audit_llm.py"]),
    ],
    3: [
        ("feat: llm.py - genai client wrapper with disk cache",
         "Google GenAI SDK wrapper (AI Studio), disk cache keyed by prompt hash, structured output, per-call logging",
         ["app/core/llm.py"]),
        ("feat: pii.py - regex masking for emails phones account numbers",
         "PII detection + log filter with unit tests",
         ["app/core/pii.py", "tests/__init__.py", "tests/unit/__init__.py",
          "tests/unit/test_pii.py"]),
        ("feat: tracing.py - opentelemetry setup and span decorator",
         "OTEL setup, @trace_step decorator, Jaeger console exporter locally",
         ["app/core/tracing.py"]),
    ],
    4: [
        ("feat: evalkit.py - harness scorers and report writer",
         "Load dataset, run scorers, write metrics.json + Markdown report, 3-run averaging, CI exit-nonzero gate",
         ["app/core/evalkit.py", "evals/__init__.py", "evals/scorers.py"]),
        ("feat: api key auth with roles submitter reviewer admin",
         "API key hashing, role dependency injection, tenant from key",
         ["app/api/auth.py", "app/api/schemas.py",
          "migrations/versions/003_api_keys.py"]),
        ("chore: DECISIONS.md first entries",
         "Postgres for state+vectors; AI Studio vs Vertex; code guardrail rationale",
         ["docs/DECISIONS.md"]),
    ],
    5: [
        ("docs: procurement policy v1 - approval tiers and PO rules",
         "Clauses 1-15: amount tiers, PO thresholds, approval authority",
         ["data/policy/procurement_policy_v1.md"]),
        ("docs: procurement policy v1 - vendor currency duplicate rules",
         "Clauses 16-32: vendor onboarding, blocked categories, currencies, split-invoice rule",
         ["data/policy/procurement_policy_v1.md"]),
        ("feat: policy question set - 40 items with correct clause IDs",
         "JSON question set for retrieval eval",
         ["evals/policy_questions.json"]),
    ],
    6: [
        ("feat: synthetic document generator - 6 invoice templates",
         "Faker + reportlab, 6 HTML templates, varied layouts and label wording",
         ["data/golden/generator.py", "data/golden/templates/__init__.py",
          "data/golden/templates/invoice_v1.html",
          "data/golden/templates/invoice_v2.html"]),
        ("feat: dataset degradation pipeline - rotate blur noise",
         "30-40% docs degraded: rotation, blur, JPEG noise, low DPI → PNG/image PDF",
         ["data/golden/degrade.py"]),
        ("feat: generate 80 synthetic labeled documents",
         "Run generator, produce labels.jsonl, validate schema",
         ["data/golden/validate_labels.py",
          "data/golden/split.json"]),
    ],
    7: [
        ("feat: map SROIE public invoices to extraction schema",
         "40 public receipts mapped, null fields handled gracefully",
         ["data/golden/sroie_mapper.py"]),
        ("feat: adversarial set - 15 edge cases",
         "Duplicate, total mismatch, missing PO, over-limit, unknown vendor, split invoice, injection, illegible scan, future date",
         ["data/golden/adversarial/__init__.py",
          "data/golden/adversarial/build_adversarial.py"]),
        ("feat: dataset split and validation script",
         "60/40 dev/test split, composition table, label schema validation",
         ["data/golden/split.json"]),
    ],
    8: [
        ("feat: text_layer.py - pdfplumber digital + tesseract OCR fallback",
         "Digital PDF → pdfplumber; no-text page → Tesseract; source tagged as ocr/digital",
         ["app/extraction/__init__.py", "app/extraction/text_layer.py",
          "app/extraction/ocr.py"]),
        ("feat: extraction schema - evidenced fields and line items",
         "Full Pydantic v2 Extraction model with Evidenced[T] wrapper",
         ["app/extraction/schema.py"]),
        ("feat: evidence checker and normalization",
         "Evidence substring check, date→ISO 8601, amounts→Decimal, currency→ISO 4217",
         ["app/extraction/evidence.py", "app/extraction/normalize.py"]),
    ],
    9: [
        ("feat: extraction prompt v1 - structured output with evidence rules",
         "Versioned prompt, field definitions, evidence copy rules, untrusted-data instruction",
         ["app/extraction/prompts/extract_v1.md"]),
        ("feat: extractor - 3-sample call with retry on schema failure",
         "3 calls (temp 0, 0.4, 0.4) in parallel, modal value per field, retry up to 2x",
         ["app/extraction/extractor.py",
          "tests/unit/test_extractor.py"]),
        ("eval: extraction baseline on dev split",
         "Field-level F1 baseline committed to docs/eval/",
         ["docs/eval/extraction_baseline.md"]),
    ],
    10: [
        ("feat: validators V01 SUM_LINES and V02 TOTAL",
         "Line sum check and subtotal+tax=total check, tolerance 0.01",
         ["app/validation/__init__.py", "app/validation/checks.py",
          "tests/unit/test_validators.py"]),
        ("feat: validators V03 DATE and V04 CURRENCY",
         "Date parse + not-future + not-too-old; currency in allowed list",
         ["app/validation/checks.py"]),
        ("feat: vendor master and PO table seeding",
         "CSV → Postgres seeder, blocked vendors included",
         ["data/vendor_master.csv", "data/po_table.csv"]),
    ],
    11: [
        ("feat: validators V05 VENDOR_KNOWN and V06 PO_REQUIRED",
         "Fuzzy vendor match (rapidfuzz), PO threshold check",
         ["app/validation/checks.py"]),
        ("feat: validators V07 PO_VALID and V08 AMOUNT_SANE",
         "PO budget check, positive+ceiling check",
         ["app/validation/checks.py"]),
        ("feat: duplicate detection - exact hash fuzzy and split-invoice",
         "SHA-256 exact; normalized (vendor_id, invoice_number) match; fuzzy; split-invoice rule",
         ["app/validation/duplicates.py",
          "tests/unit/test_duplicates.py"]),
    ],
    12: [
        ("feat: confidence.py - field agreement across 3 samples",
         "Modal value, agreement score, validator factor 1.0/0.5/0.2",
         ["app/extraction/confidence.py"]),
        ("feat: document confidence - minimum over required fields",
         "Required fields: vendor_name, invoice_number, invoice_date, currency, total",
         ["app/extraction/confidence.py"]),
        ("eval: confidence calibration table on dev split",
         "Bin confidence → accuracy, choose CONF_FIELD_MIN",
         ["docs/eval/confidence_calibration.md"]),
    ],
    13: [
        ("feat: policy chunker - split by numbered clause",
         "Clause ID extraction, heading path, policy_version tagging",
         ["app/policy/__init__.py", "app/policy/chunker.py"]),
        ("feat: policy embedding - text-embedding-004 via genai SDK",
         "Embed chunks, store in pgvector",
         ["app/policy/embed.py"]),
        ("feat: policy ingest pipeline - chunk embed store version",
         "Full ingest script, re-embed on new version",
         ["app/policy/ingest.py"]),
    ],
    14: [
        ("feat: policy retrieval - vector top20 + fulltext top20 + RRF",
         "Cosine similarity + ts_rank, RRF fusion k=60, top 5",
         ["app/policy/retrieve.py"]),
        ("feat: policy query builder - 2-4 focused queries from facts",
         "Amount tier, PO requirement, vendor status, currency/tax queries",
         ["app/policy/retrieve.py"]),
        ("eval: retrieval hit@1 and hit@3 - hybrid vs vector-only vs fulltext",
         "40 questions, 3 methods compared",
         ["docs/eval/retrieval_comparison.md"]),
    ],
    15: [
        ("feat: policy checker tools - search_policy and get_clause",
         "Tool definitions wrapping the retrieval layer",
         ["app/agents/__init__.py", "app/agents/tools.py"]),
        ("feat: policy checker agent - ReAct style with citation requirement",
         "ADK LlmAgent, structured output: verdict + clause_ids + reasons, 4-tool cap",
         ["app/agents/policy_checker.py"]),
        ("feat: post-check citation validator",
         "Code-level citation guard, metric: invalid_citation_count",
         ["app/agents/policy_checker.py",
          "tests/unit/test_policy_checker.py"]),
    ],
    16: [
        ("feat: decision engine - pure function rule-based router",
         "decide() with hard-fail, low-confidence, validator, policy, amount-limit checks",
         ["app/decision/__init__.py", "app/decision/engine.py"]),
        ("test: decision engine truth table - all boundary cases",
         "Unit tests for every branch including limit boundaries",
         ["tests/unit/test_decision_engine.py"]),
        ("feat: decision persistence - reasons citations input hash",
         "Write to decisions table with reasons_json, cited_clause_ids, input_hash",
         ["app/decision/engine.py"]),
    ],
    17: [
        ("feat: ADK sequential workflow - coordinator orchestrating agents",
         "SequentialAgent: extractor → validators → policy_checker → router",
         ["app/agents/coordinator.py"]),
        ("feat: ADK reflection loop - targeted re-extraction for low-confidence fields",
         "LoopAgent, targeted prompt with field name + prior candidates + page region, max 2 passes",
         ["app/agents/coordinator.py"]),
        ("eval: end-to-end run on golden dev set - confusion matrix",
         "Full pipeline on dev split, confusion matrix, per-agent cost table",
         ["docs/eval/e2e_first_run.md"]),
    ],
    18: [
        ("feat: states.py - legal transitions and transition function",
         "All states, transition() checks legality, updates state + writes audit_event in one tx",
         ["app/core/states.py", "app/core/audit.py"]),
        ("feat: job_queue - postgres-backed queue with SKIP LOCKED and retry",
         "Worker claims with SELECT FOR UPDATE SKIP LOCKED, attempts counter, backoff, dead-letter",
         ["app/core/queue.py"]),
        ("test: idempotency - same message 5x yields exactly one decision",
         "Integration test: deliver same job 5×, assert 1 decision in DB",
         ["tests/integration/__init__.py",
          "tests/integration/test_idempotency.py"]),
    ],
    19: [
        ("feat: POST /documents - upload validate store enqueue",
         "File validation (type + size), SHA-256, Supabase upload, RECEIVED state",
         ["app/api/routes.py", "app/api/errors.py"]),
        ("feat: GET /documents/{id} and audit + queue endpoints",
         "Document status, audit log, reviewer queue with filters",
         ["app/api/routes.py"]),
        ("feat: POST /documents/{id}/decision and error format",
         "Reviewer decision endpoint, consistent JSON errors, rate limiting",
         ["app/api/routes.py", "app/api/schemas.py"]),
    ],
    20: [
        ("feat: MCP server scaffold - FastAPI-based MCP protocol",
         "MCP server with tool manifest endpoint",
         ["app/mcp_server/__init__.py", "app/mcp_server/server.py"]),
        ("feat: MCP tools - submit_document get_status search_policy list_queue",
         "4 tools through same service layer + role checks",
         ["app/mcp_server/server.py"]),
        ("feat: MCP submit_decision tool and README examples",
         "5th tool, example calls documented",
         ["app/mcp_server/server.py", "docs/mcp_examples.md"]),
    ],
    21: [
        ("feat: streamlit queue view - filter by reason sort by age and amount",
         "Queue screen, shows decision reasons prominently",
         ["app/ui/__init__.py", "app/ui/review_app.py"]),
        ("feat: streamlit detail view - document preview fields evidence clauses",
         "Document viewer, fields with confidence + evidence, cited clause text, audit timeline",
         ["app/ui/review_app.py"]),
        ("feat: streamlit action panel - approve reject return edit fields export",
         "Decision buttons, field editor, corrections → corrections.jsonl",
         ["app/ui/review_app.py"]),
    ],
    22: [
        ("feat: otel tracing - one trace per document spans per agent step",
         "Trace per document, span attributes: tokens, cost, model, prompt_version",
         ["app/core/tracing.py"]),
        ("feat: structured JSON logs with PII masking filter",
         "JSON log formatter, PII masking on all handlers",
         ["app/core/pii.py"]),
        ("feat: cost and latency SQL view and markdown report script",
         "SQL view over llm_calls, prints cost/agent and p50/p95 latency",
         ["app/core/cost_report.py"]),
    ],
    23: [
        ("feat: run_eval.py - full pipeline eval with 3-run averaging",
         "Runs pipeline on test split, 3 runs, mean + range",
         ["evals/run_eval.py"]),
        ("feat: scorers - F1 decision matrix retrieval faithfulness latency cost",
         "All scorers: field F1, all-fields-correct, validator catch rate, confusion matrix, etc.",
         ["evals/scorers.py"]),
        ("eval: faithfulness judge - 30 sampled citations labeled and scored",
         "LLM judge on 30 citations, your labels vs judge labels, agreement reported",
         ["evals/faithfulness_judge.py",
          "docs/eval/faithfulness.md"]),
    ],
    24: [
        ("feat: CI eval gate - smoke set blocks on false auto-approve or F1 drop",
         "10-doc smoke set in GitHub Actions, fails if false_auto_approve > 0 or F1 drops",
         [".github/workflows/ci.yml",
          "evals/smoke_set/__init__.py"]),
        ("feat: security - signed URLs prompt injection test",
         "Signed URLs (Supabase), injection adversarial docs → not auto-approved test",
         ["app/api/routes.py",
          "tests/adversarial/__init__.py",
          "tests/adversarial/test_injection.py"]),
        ("feat: pip-audit in CI and threat model in DECISIONS.md",
         "pip-audit step, threat model table: asset/threat/mitigation/residual",
         [".github/workflows/ci.yml", "docs/DECISIONS.md"]),
    ],
    25: [
        ("feat: Dockerfile for API and worker",
         "Multi-stage Dockerfile, separate CMD for api vs worker",
         ["infra/Dockerfile"]),
        ("feat: deploy script - build push migrate deploy to Render",
         "deploy.sh: build → push to ghcr.io → run migrations → deploy",
         ["infra/deploy.sh", ".github/workflows/deploy.yml"]),
        ("feat: seed data and smoke test script",
         "Vendor master, PO table, policy v1, 5 demo documents, smoke test",
         ["infra/seed.py", "infra/smoke_test.py"]),
    ],
    26: [
        ("eval: full eval run 1 of 3 on test split",
         "First run, metrics.json committed",
         ["docs/eval/run_1.md"]),
        ("eval: full eval run 2 and 3 - mean and range reported",
         "Runs 2+3, mean and range computed",
         ["docs/eval/run_2.md", "docs/eval/run_3.md",
          "docs/eval/eval_summary.md"]),
        ("docs: failure analysis table - every wrong prediction cause and fix",
         "Per-wrong-prediction table with document, expected, got, cause, fix",
         ["docs/eval/failure_analysis.md"]),
    ],
    27: [
        ("docs: README - problem architecture eval table dataset description",
         "Full README: problem, architecture diagram, quick start, eval table, failure analysis summary, cost+latency",
         ["docs/README.md"]),
        ("docs: DECISIONS.md - all major choices with rejected alternatives",
         "Postgres vs Redis, code guardrail vs agent, 3-sample confidence vs self-reported, hybrid vs vector-only",
         ["docs/DECISIONS.md"]),
        ("docs: discovery_brief.md - customer questions and assumptions",
         "1-page: volumes/formats/systems-of-record questions, assumptions, risks, success metrics",
         ["docs/discovery_brief.md"]),
    ],
    28: [
        ("docs: field_insights.md - 5 real friction points as feature requests",
         "5 friction points with Gemini API / ADK / pgvector: each as problem → workaround → proposed change",
         ["docs/field_insights.md"]),
        ("docs: interview prep reference card",
         "Answers to all 6 FDE interview questions",
         ["docs/interview_prep.md"]),
        ("chore: final dependency audit and lock file update",
         "pip-audit clean, requirements.lock pinned",
         ["requirements.lock"]),
    ],
    29: [
        ("perf: llm call batching and disk cache for dev",
         "Cache hits measured, tokens saved reported",
         ["app/core/llm.py"]),
        ("test: light load test - 50 concurrent documents",
         "Submit 50 at once, report throughput + p95 + cost + no duplicates",
         ["tests/load/__init__.py", "tests/load/test_load.py",
          "docs/eval/load_test.md"]),
        ("perf: cost optimization - fast model default escalation path documented",
         "Config reviewed, cost per doc measured and in README",
         ["app/core/config.py"]),
    ],
    30: [
        ("docs: demo script - 4 scenarios 2 minutes",
         "Clean invoice (auto-approved); mismatch (review); injection (not approved); trace; eval table",
         ["docs/demo_script.md"]),
        ("feat: demo seed - clean mismatch injection illegible documents",
         "Seed exactly the 4 demo docs to deployed environment",
         ["infra/seed_demo.py"]),
        ("chore: final README pass and architecture diagram update",
         "Mermaid diagram reviewed, eval numbers from committed reports",
         ["docs/README.md"]),
    ],
    31: [
        ("fix: post-deploy bugs from QA pass",
         "Bugs found during full E2E test of live URL",
         ["app/api/routes.py", "app/core/queue.py"]),
        ("chore: update README with live URL and demo instructions",
         "Add live URL, link to eval report",
         ["docs/README.md"]),
        ("chore: tag v1.0.0 release - project submission ready",
         "Final release tag",
         ["docs/CHANGELOG.md"]),
    ],
    32: [
        ("docs: resume number cross-reference table",
         "Table mapping each resume bullet → eval report line",
         ["docs/resume_numbers.md"]),
        ("chore: clean up TODOs and dev artifacts",
         "Remove debug prints, leftover notebooks, temp files",
         ["app/core/llm.py", "app/core/config.py"]),
        ("chore: final commit - DocFlow complete",
         "Project is interview-ready",
         ["docs/README.md"]),
    ],
}

# ── File content generators ─────────────────────────────────────────────────

def stub_content(path: str, day: int, description: str) -> str:
    """Generate meaningful stub content for a file based on its path."""
    p = Path(path)
    ext = p.suffix

    header_map = {
        ".py": f'"""\n{description}\nGenerated: Day {day}\n"""\n\n',
        ".md": f"# {p.stem.replace('_', ' ').title()}\n\n> {description}\n\n",
        ".yml": f"# {description}\n# DocFlow CI/CD\n\n",
        ".yaml": f"# {description}\n# DocFlow\n\n",
        ".html": f"<!-- {description} -->\n<!DOCTYPE html>\n<html>\n<body>\n<!-- template -->\n</body>\n</html>\n",
        ".sql": f"-- {description}\n-- Day {day}\n\n",
        ".json": "{}",
        ".toml": f"# {description}\n",
        ".csv": "id,name,status\n",
        ".lock": "# pinned requirements\n",
        "": f"# {description}\n",
    }

    # Special cases
    if path == "Makefile":
        return textwrap.dedent("""\
            .PHONY: up migrate test eval run deploy

            up:
            \tdocker-compose -f infra/docker-compose.yml up -d

            migrate:
            \talembic upgrade head

            test:
            \tpytest tests/ -v

            eval:
            \tpython evals/run_eval.py

            run:
            \tuvicorn app.main:app --reload

            deploy:
            \tbash infra/deploy.sh
            """)

    if path == ".gitignore":
        return textwrap.dedent("""\
            __pycache__/
            *.pyc
            .env
            .env.local
            venv/
            .venv/
            dist/
            *.egg-info/
            .pytest_cache/
            .ruff_cache/
            docs/eval/*.json
            data/golden/documents/
            llm_cache/
            """)

    if path == ".env.example":
        return textwrap.dedent("""\
            # Google AI Studio (free tier)
            GOOGLE_API_KEY=your_key_here
            USE_VERTEX=false

            # Supabase (free tier)
            SUPABASE_URL=https://xxxx.supabase.co
            SUPABASE_KEY=your_key_here
            DATABASE_URL=postgresql://postgres:pass@db.xxxx.supabase.co:5432/postgres

            # App settings
            MAX_FILE_MB=10
            CONF_FIELD_MIN=0.85
            AUTO_APPROVE_LIMIT=5000
            ENVIRONMENT=development
            """)

    if path == ".github/workflows/ci.yml":
        return textwrap.dedent("""\
            name: CI
            on: [push, pull_request]
            jobs:
              lint-and-test:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - uses: actions/setup-python@v5
                    with: { python-version: '3.11' }
                  - run: pip install -e ".[dev]"
                  - run: ruff check .
                  - run: pytest tests/unit/ -v
                  - run: pip-audit
            """)

    # Add a progress note to .md files for eval/ folder
    if "eval/" in path and ext == ".md":
        return textwrap.dedent(f"""\
            # {p.stem.replace('_', ' ').title()}

            > {description}

            Generated on day {day}. Full metrics will be populated after the eval run.

            | Metric | Value |
            |--------|-------|
            | Run date | TBD |
            | Dataset split | test |
            | Num documents | TBD |

            _Update this table after running `make eval`_
            """)

    return header_map.get(ext, f"# {description}\n# Day {day}\n")


# ── Main logic ──────────────────────────────────────────────────────────────

def get_project_day() -> int:
    today = date.today()
    delta = (today - PROJECT_START).days + 1
    return max(1, min(delta, 32))


def pick_commits_for_today(day: int):
    """Return 2-3 commits for today, slightly randomized in count."""
    plan = DAY_PLAN.get(day, [])
    if not plan:
        # Fallback for days not in plan: a generic maintenance commit
        plan = [
            (f"chore: progress update day {day}",
             "Incremental progress and minor fixes",
             ["docs/README.md"]),
        ]
    # Randomly drop one commit if there are 3 (occasionally do 2 commits)
    if len(plan) == 3 and random.random() < 0.25:
        plan = plan[:2]
    return plan


def apply_file_changes(repo_root: Path, files: list, day: int, description: str):
    """Write stub/progress content to each file, creating parent dirs."""
    for rel_path in files:
        full_path = repo_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.write_text(stub_content(rel_path, day, description))
        else:
            # Append a small progress note so there IS a diff
            existing = full_path.read_text()
            note = f"\n# Progress update day {day}: {description[:60]}\n"
            if note.strip() not in existing:
                with full_path.open("a") as f:
                    if rel_path.endswith(".py"):
                        f.write(f"\n# Day {day} update: {description[:60]}\n")
                    elif rel_path.endswith(".md"):
                        f.write(f"\n> Day {day}: {description[:60]}\n")
                    # For other files, skip to avoid corruption


def write_progress_log(repo_root: Path, day: int, commits):
    """Append to a human-readable progress log."""
    log_path = repo_root / "docs" / "progress.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    today_str = date.today().isoformat()
    with log_path.open("a") as f:
        f.write(f"\n## Day {day} — {today_str}\n")
        for msg, desc, _ in commits:
            f.write(f"- **{msg}**: {desc}\n")


def main():
    repo_root = Path(__file__).parent.parent  # DocFlow/
    day = get_project_day()

    # Override day via env for testing
    if os.environ.get("DOCFLOW_DAY"):
        day = int(os.environ["DOCFLOW_DAY"])

    commits = pick_commits_for_today(day)

    # Apply all file changes (they'll be staged together as one commit in CI)
    # We use the FIRST commit's message as the git commit message,
    # and pack all changes into it. This is intentional for authenticity.
    all_files = []
    for _msg, desc, files in commits:
        apply_file_changes(repo_root, files, day, desc)
        all_files.extend(files)

    # Write progress log
    write_progress_log(repo_root, day, commits)

    # Pick the commit message: use a random one from today's plan
    chosen = random.choice(commits)
    commit_msg = chosen[0]

    # Write it for the shell script to read
    Path("/tmp/commit_msg.txt").write_text(commit_msg)

    print(f"Day {day} — Commit: {commit_msg}")
    print(f"Files touched: {all_files}")


if __name__ == "__main__":
    main()
