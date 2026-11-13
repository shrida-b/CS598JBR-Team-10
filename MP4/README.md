# MP4 – Agentic C → Rust Translation (Group 10)

| | Project | C source | CRUST-Bench Rust spec |
|---|---|---|---|
| project_1 | **expr** | `subjects/project_1/` | `benchmark/RBench/expr/` (2 tests) |
| project_2 | **rbtree-lab** | `subjects/project_2/` | `benchmark/RBench/rbtree_lab/` (7 tests) |

All models, endpoints and tools used here are **free**: free-tier API keys only, no
paid credits.

> **Status:** Task 1 (setup, configs, structure, environment check) is complete.
> The translation controller `src/run_pipeline.py` comes in Task 2. Its interface
> below is already fixed by `configs/`.

## Directory layout

```
MP4/
├── README.md
├── requirements.txt     # stdlib only (nothing to pip install)
├── src/
│   └── check_setup.py   # verifies toolchain, configs, spec builds, API keys + tool calling
├── configs/
│   ├── pipeline.toml    # providers/models, inference settings, agent loop, stopping condition,
│   │                    # evaluation commands, integrity guards, log redaction
│   ├── projects.toml    # per-project paths/metadata (no per-function hints)
│   ├── tools.json       # function-calling schemas of the tools exposed to the agent
│   ├── prompts/         # system.md, translate.md (iteration 1), repair.md (iterations 2..N)
│   └── .env.example     # names of required env vars (real configs/.env is git-ignored)
├── benchmark/RBench/    # (addition) unmodified CRUST-Bench Rust interfaces + tests
├── subjects/            # original C projects: project_1 = expr, project_2 = rbtree-lab
├── translations/        # final generated Rust crates (project_1/, project_2/)
└── trajectories/        # per-project execution logs (project_1/, project_2/)
```

## Models, frameworks and tools used

| Component | What we use | Version / details |
|---|---|---|
| Agentic framework | **`crust-agent`**, our own Python controller (no third-party agent framework). It runs an OpenAI-compatible function-calling agent loop inside an outer evaluate → repair loop | v0.1.0, Python 3.13.1 standard library only |
| Primary provider | **Google Gemini API, free tier** (Google AI Studio key) via its OpenAI-compatible endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Primary model | `gemini-3.8-flash` | "Stable", free of charge on the free tier |
| Gemini fallbacks (in order) | `gemini-4-hydrogen`, `gemini-3.6-flash` | free-tier models; used on 429/5xx/unavailable |
| Secondary provider | **OpenRouter**, free `:free` endpoints (OpenAI-compatible) | `https://openrouter.ai/api/v1` |
| OpenRouter models (in order) | `nvidia/nemotron-3-ultra-550b-a55b:free`, `cohere/north-mini-code:free`, `google/gemma-4-31b-it:free` | used only if the Gemini quota runs out mid-run |
| Optional local runtime | **Ollama** (OpenAI-compatible endpoint `localhost:11434/v1`), `qwen2.5-coder:7b` | Ollama 0.40.4; not used by default (8 GB RAM limits it to ~7B models) |
| Rust toolchain | `nightly-2025-05-13`: rustc 1.89.0-nightly (8405332bd 2025-05-12), cargo 1.89.0-nightly (056f5f4f3 2025-05-09) | same toolchain as grading |
| Linter | Clippy 0.1.88 (8405332bdf 2025-05-12), categories correctness / style / complexity / perf | |
| Safety analysis | Instructional team's unsafe-metrics tool (set `[unsafe_metrics].command` once released). Until then, a built-in approximate scanner in `src/` | |
| Benchmark | CRUST-Bench (`github.com/anirudhkhatry/CRUST-bench`, `datasets/CRUST_bench.zip`) | C from `CBench/`, Rust spec from `RBench/` |

A **single agent** runs with **one active model** at a time. Fallback models take
over only when the current one is rate-limited or unavailable. Each saved request
in the trajectories records which model served it.

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
- rustup with `nightly-2025-05-13` + `clippy`, `rustfmt`
- Ollama 0.40.4 (optional)

## Tools available to the agent (`configs/tools.json`)

The agent works in a sandboxed view: `c/` is the original C project (read-only) and
`rust/` is the crate being written. It has **no arbitrary shell**.

| Tool | Purpose |
|---|---|
| `list_files`, `read_file`, `search` | inspect the C project, the Rust interface, and the tests |
| `write_file`, `replace_in_file` | modify Rust code. Writes are limited to `rust/src/`; `src/bin/**` (tests) and `Cargo.lock` are protected |
| `cargo` (`check` \| `build` \| `test` \| `clippy`) | always runs `cargo +nightly-2025-05-13 …`. Clippy uses the graders' 4 categories and reports per-category counts |
| `unsafe_metrics` | unsafe lines / calls / casts / pointer arithmetic, with locations |
| `finish` | ends the iteration; the controller then evaluates independently |

## Pipeline overview

```
            ┌──────────── controller (src/, configs/pipeline.toml) ─────────────┐
 setup:     copy benchmark spec → translations/project_N, interfaces/<m>.rs → src/<m>.rs
            │                                                                   │
 iter k:    prompt = system.md + (translate.md if k=1 else repair.md+feedback)  │
            ▼                                                                   │
     ┌─ agent session (≤25 model calls) ──────────────────────────┐             │
     │ read C / interface / tests → write Rust → cargo check/test │             │
     │ → clippy → unsafe_metrics → repair … → finish              │             │
     └────────────────────────────────────────────────────────────┘             │
            ▼                                                                   │
 evaluate:  integrity guard (tests + Cargo.lock unchanged, pub signatures kept, │
            no FFI) → cargo build → cargo test → clippy (4 categories) →         │
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
errors, failing tests with assertion messages, Clippy warnings per category, unsafe
locations, integrity violations) into `prompts/repair.md`.

**Score** (used for the best snapshot and for measuring progress), compared
lexicographically: builds → tests passed → −(primary unsafe total) → −(Clippy total).

## Stopping condition

After each iteration, the run stops at the first of these that is true:

1. **Success:** integrity checks pass, `cargo build` succeeds, all tests pass,
   all four primary unsafe metrics are 0, and Clippy total ≤ 0.
2. **Iteration cap:** 6 outer iterations (`max_iterations`).
3. **No progress:** the score has not improved for 2 consecutive iterations (`no_progress_patience`).
4. **Request budget:** the provider's `max_requests_per_run` is used up (Gemini
   200; OpenRouter 45, which keeps it under its free daily cap). The run
   checkpoints, and re-running the same command resumes it.

The final translation is the best-scoring snapshot, not necessarily the last one.

## Installation

```bash
# 1. Rust toolchain used for translation, repair and grading
rustup toolchain install nightly-2025-05-13 --component clippy,rustfmt

# 2. Python 3.11+ (no third-party packages: requirements.txt is stdlib only)
python3 --version

# 3. Free API keys (never commit them; configs/.env is git-ignored)
#    Gemini:     https://aistudio.google.com/apikey   (primary)
#    OpenRouter: https://openrouter.ai/keys           (secondary)
cp MP4/configs/.env.example MP4/configs/.env    # fill in GEMINI_API_KEY / OPENROUTER_API_KEY

# 4. (optional) local model
ollama pull qwen2.5-coder:7b

# 5. Verify everything: toolchain, configs, specs compile, keys + tool calling work
cd MP4 && python3 src/check_setup.py
```

## Running the pipeline

```bash
cd MP4
python3 src/run_pipeline.py --project project_1                       # expr
python3 src/run_pipeline.py --project project_2                       # rbtree-lab
python3 src/run_pipeline.py --project project_1 --provider openrouter  # override provider
```

Output goes to `translations/project_N/` (the Rust crate) and
`trajectories/project_N/` (model messages, tool calls, per-iteration feedback and
diffs, and `summary.json`). API keys are redacted from every log before it is
written.

Evaluating a final translation by hand:

```bash
cd MP4/translations/project_1
cargo +nightly-2025-05-13 build
cargo +nightly-2025-05-13 test
cargo +nightly-2025-05-13 clippy --all-targets --all-features -- \
    -W clippy::correctness -W clippy::style -W clippy::complexity -W clippy::perf
```

## API / usage limits affecting the experiment

- **Gemini free tier:** quotas apply per Google Cloud project, not per key, and
  requests-per-day resets at midnight Pacific. Google's docs do not publish free-tier
  numbers for these models; they are shown only in AI Studio
  (`aistudio.google.com/rate-limit`). The pipeline therefore uses conservative
  defaults (8 req/min, 200 requests per run) and backs off 60 s on HTTP 429.
  Free-tier prompts may be used by Google to improve its products. The inputs here
  are only public benchmark code.
- **OpenRouter free variants** (docs, Nov 2026): **20 requests/min**, and
  **50 requests/day** for accounts with fewer than 10 purchased credits (we bought
  none). The pipeline throttles to 18 req/min and caps a run at 45 requests.
- If a provider's free quota runs out mid-run, the controller switches to the next
  provider in `provider_fallbacks` or checkpoints and stops. Either way, the switch
  is logged in the trajectory.
- Free-model availability changes over time. Fallbacks cover this, and the serving
  model is logged per request.
- Local Ollama has no rate limit, but 8 GB of RAM restricts it to ~7B models.

## Credentials

No keys are stored in the repository. `configs/.env` is git-ignored. Every
trajectory is scrubbed of the `GEMINI_API_KEY` / `OPENROUTER_API_KEY` values and of
key-shaped patterns (`AIza…`, `sk-or-…`, `Bearer …`) before it is saved.
