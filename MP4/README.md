# MP4 – Agentic C → Rust Translation (Group 10)

| | Project | C source | CRUST-Bench Rust spec |
|---|---|---|---|
| project_1 | **expr** | `subjects/project_1/` | `benchmark/RBench/expr/` |
| project_2 | **rbtree-lab** | `subjects/project_2/` | `benchmark/RBench/rbtree_lab/` |

All models, endpoints and tools used here are **free**: no paid API, no paid credits.

> **Status:** Task 1 (setup, configs, structure) is complete. The pipeline code in
> `src/` comes in Task 2. The commands below describe its intended interface, as
> defined by `configs/`.

## Directory layout

```
MP4/
├── README.md
├── requirements.txt     # stdlib only (nothing to pip install)
├── src/                 # pipeline controller (Python) – launches/controls the agent loop
├── configs/
│   ├── pipeline.toml    # model/provider, inference settings, loop + stopping condition, eval commands
│   ├── projects.toml    # per-project paths/metadata (no per-function hints)
│   ├── tools.json       # function-calling schemas of the tools exposed to the agent
│   ├── prompts/         # system.md, translate.md (iteration 1), repair.md (iterations 2..N)
│   └── .env.example     # names of required env vars (real .env is git-ignored)
├── benchmark/RBench/    # (addition) unmodified CRUST-Bench Rust interfaces + tests
├── subjects/            # original C projects (project_1 = expr, project_2 = rbtree-lab)
├── translations/        # final generated Rust crates (project_1/, project_2/)
└── trajectories/        # per-project execution logs (project_1/, project_2/)
```

## Models, frameworks and tools used

| Component | What we use | Version / details |
|---|---|---|
| Agentic framework | **`crust-agent`**, our own Python controller (no third-party agent framework). It runs an OpenAI-compatible function-calling loop plus an outer evaluate → repair loop | v0.1.0, Python 3.13.1 standard library only |
| Model provider | **OpenRouter** free endpoints (`:free` variants), OpenAI-compatible Chat Completions API | `https://openrouter.ai/api/v1` |
| Primary model | `nvidia/nemotron-3-ultra-550b-a55b:free` | 1M context, tool calling |
| Fallback models (in order) | `cohere/north-mini-code:free`, `google/gemma-4-31b-it:free` | used only when the primary is rate-limited or unavailable |
| Optional local runtime | **Ollama** (OpenAI-compatible endpoint `localhost:11434/v1`), model `qwen2.5-coder:7b` | Ollama 0.40.4. Not the main backend: the 8 GB Mac can only hold ~7B models |
| Rust toolchain | `nightly-2025-05-13` (rustc 1.89.0-nightly 8405332bd 2025-05-12, cargo 1.89.0-nightly 056f5f4f3 2025-05-09) | same toolchain the graders use |
| Linter | Clippy 0.1.88 (8405332bdf 2025-05-12), categories correctness / style / complexity / perf | |
| Safety analysis | Instructional team's unsafe-metrics tool (configured in `pipeline.toml [unsafe_metrics]` once released). Until then, a built-in approximate scanner in `src/` | |
| Benchmark | CRUST-Bench (`anirudhkhatry/CRUST-bench`, `datasets/CRUST_bench.zip`) | C from `CBench/`, Rust spec from `RBench/` |

The exact model that answered each request is recorded per call in the trajectories,
because OpenRouter returns the serving model in each response.

## Inference settings (`configs/pipeline.toml [inference]`)

| Setting | Value |
|---|---|
| temperature | 0.2 |
| top_p | 0.95 |
| max_tokens per response | 8192 |
| seed | 598 (sent when the provider supports it) |
| tool_choice / parallel tool calls | `auto` / disabled |
| request timeout | 300 s |
| model calls per agent iteration | ≤ 25 |
| tool output shown to the model | truncated to 12,000 chars (head and tail kept) |

## OS / runtime

- macOS 14.5 (23F79), Apple M3 (arm64), 8 GB RAM
- Python 3.13.1 (3.11+ required for `tomllib`)
- rustup with `nightly-2025-05-13` + `clippy`, `rustfmt` components
- Ollama 0.40.4 (optional)

## Tools available to the agent (`configs/tools.json`)

The agent works in a sandboxed view: `c/` is the original C project (read-only) and
`rust/` is the crate being written. It gets **no arbitrary shell**.

| Tool | Purpose |
|---|---|
| `list_files`, `read_file`, `search` | inspect the C project, the Rust interface, and the tests |
| `write_file`, `replace_in_file` | modify Rust code. Writes are limited to `rust/src/`; `src/bin/**` (tests) and `Cargo.lock` are protected |
| `cargo` (`check` \| `build` \| `test` \| `clippy`) | always runs `cargo +nightly-2025-05-13 …`. Clippy uses the graders' 4 categories and returns per-category counts |
| `unsafe_metrics` | unsafe lines / calls / casts / pointer arithmetic, with locations |
| `finish` | ends the iteration; the controller then evaluates independently |

## Pipeline overview

```
            ┌──────────── controller (src/, configs/pipeline.toml) ─────────────┐
 setup:     copy benchmark spec → translations/project_N, interfaces/<m>.rs → src/<m>.rs
            │                                                                   │
 iter k:    prompt (translate.md if k=1, else repair.md + feedback report)      │
            │                                                                   │
            ▼                                                                   │
     ┌─ agent session (≤25 model calls) ──────────────────────────┐             │
     │ read C / interface / tests → write Rust → cargo check/test │             │
     │ → clippy → unsafe_metrics → repair … → finish              │             │
     └────────────────────────────────────────────────────────────┘             │
            ▼                                                                   │
 evaluate:  integrity guard (tests + Cargo.lock unchanged, pub signatures kept, │
            no FFI) → cargo build → cargo test → clippy ×4 categories →          │
            unsafe metrics → score; save feedback + diff to trajectories/       │
            ▼                                                                   │
 stop? ── no ──► keep best snapshot, feed report into next repair prompt ───────┘
   │yes
   ▼
 final crate in translations/project_N, summary.json in trajectories/project_N
```

**Feedback path.** Inside a session, the agent sees raw (truncated) compiler, test,
Clippy and unsafe-metrics output as tool results. Between sessions, the controller
re-runs everything itself and puts a structured report (status table, compile
errors, failing tests with assertion messages, Clippy warnings by category, unsafe
locations, integrity violations) into `prompts/repair.md`. A single agent and a
single active model are used; fallback models only take over when the primary is
unavailable.

**Score** (for "best snapshot" and progress), compared lexicographically:
builds → tests passed → −(primary unsafe total) → −(Clippy total).

## Stopping condition

After each iteration, the run stops at the first of these that is true:

1. **Success:** integrity checks pass, `cargo build` succeeds, all tests pass,
   all four primary unsafe metrics are 0, and Clippy total ≤ 0.
2. **Iteration cap:** 6 outer iterations (`max_iterations`).
3. **No progress:** the score has not improved for 2 consecutive iterations (`no_progress_patience`).
4. **Request budget:** 45 model requests per run (`max_requests_per_run`). This
   keeps a run under OpenRouter's free daily cap. The run checkpoints, and
   re-running the same command resumes it.

The final translation is the best-scoring snapshot, not necessarily the last one.

## Installation

```bash
# 1. Rust toolchain used for translation, repair and grading
rustup toolchain install nightly-2025-05-13 --component clippy,rustfmt

# 2. Python 3.11+ (no third-party packages: requirements.txt is stdlib only)
python3 --version

# 3. Free OpenRouter key (https://openrouter.ai/keys) – never commit it
cp MP4/configs/.env.example MP4/configs/.env    # then fill in OPENROUTER_API_KEY
# or: export OPENROUTER_API_KEY=...

# 4. (optional) local fallback model
ollama pull qwen2.5-coder:7b
```

## Running the pipeline

```bash
cd MP4
python3 src/run_pipeline.py --project project_1          # expr
python3 src/run_pipeline.py --project project_2          # rbtree-lab
python3 src/run_pipeline.py --project project_1 --provider ollama   # local fallback
```

Output goes to `translations/project_N/` (the Rust crate) and
`trajectories/project_N/` (model messages, tool calls, per-iteration feedback, diffs,
and `summary.json`). API keys are redacted from every log before it is written.

Evaluating a final translation by hand:

```bash
cd MP4/translations/project_1
cargo +nightly-2025-05-13 build
cargo +nightly-2025-05-13 test
cargo +nightly-2025-05-13 clippy --all-targets --all-features -- \
    -W clippy::correctness -W clippy::style -W clippy::complexity -W clippy::perf
```

## API / usage limits affecting the experiment

- **OpenRouter free variants** (docs, Nov 2026): **20 requests/min**, and
  **50 requests/day** for accounts with fewer than 10 purchased credits (1000/day
  with ≥ 10). We bought no credits, so the 50/day cap is binding. The pipeline
  throttles to 18 req/min, caps a run at 45 requests, backs off 65 s on HTTP 429,
  and resumes from a checkpoint. As a result, a full run of one project may span
  more than one day.
- Free-endpoint availability changes over time. If the primary model is unavailable,
  the configured fallbacks are used, and the trajectories record which model served
  each request.
- Local Ollama has no rate limit, but 8 GB of RAM restricts it to ~7B models.

## Credentials

No keys are stored in the repository. `configs/.env` is git-ignored, and every
trajectory is scrubbed of `OPENROUTER_API_KEY` values and `sk-or-…` / `Bearer …`
patterns before it is saved.
