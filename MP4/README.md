# MP4: Agentic C-to-Rust Translation (Group 10)

| | Project | C source | CRUST-Bench Rust spec |
|---|---|---|---|
| project_1 | **expr** | `subjects/project_1/` | `benchmark/RBench/expr/` (2 tests) |
| project_2 | **rbtree-lab** | `subjects/project_2/` | `benchmark/RBench/rbtree_lab/` (6 tests; a 7th is commented out) |

All models, endpoints and tools used here are **free**: free-tier API keys only, no
paid credits.

> **Status:** Tasks 1–3 are complete, and the Task 4 report text is in
> `PROGRESS_REPORT_MP4.tex` / `.md`. Both final translations build, pass every
> benchmark test, score 0 on all unsafe metrics from the course NewMetrics tool, and
> have 0 Clippy warnings in the translated code. Both come from the final pipeline:
> project_1 ran before the last `llm.py` change, which only affects retries after a
> network timeout. See `trajectories/project_<N>/TRAJECTORY.md`; earlier development
> runs are kept in `trajectories/project_<N>/previous_runs/`.

## Environment

### Agentic framework, models and tools

| Component | What we use | Version / details |
|---|---|---|
| Agentic framework | **`crust-agent`**, our own Python controller (no third-party agent framework). It runs an OpenAI-compatible function-calling agent loop inside an outer evaluate → repair loop | v0.1.0, Python 3.13.1 standard library only |
| Primary provider | **Google Gemini API, free tier** (Google AI Studio key) via its OpenAI-compatible endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Gemini models: quota-aware cascade, tried in this order | 1. `gemini-4-hydrogen` 2. `gemini-3.8-flash` 3. `gemini-3.6-flash` 4. `gemini-3-flash-preview` (5 RPM / 20 RPD each) → 5. `gemini-3.5-flash-lite` 6. `gemini-3.1-flash-lite` (15 RPM / 500 RPD each) | All free tier. The stronger Flash models are used while their daily quota lasts, then the high-volume Flash-Lite models. A model is skipped for the day once its RPD runs out or it returns a daily 429. A 5xx "high demand" response is retried after 10 s and 20 s, then the model is skipped. A hung or dropped connection benches the model for 30 min |
| Secondary provider | **OpenRouter**, free `:free` endpoints (OpenAI-compatible) | `https://openrouter.ai/api/v1` |
| OpenRouter models (in order) | `nvidia/nemotron-3-ultra-550b-a55b:free`, `cohere/north-mini-code:free`, `google/gemma-4-31b-it:free` | Used only if every Gemini model is out of quota, or with `--provider openrouter` |
| Optional local runtime | **Ollama** (OpenAI-compatible endpoint `localhost:11434/v1`), `qwen2.5-coder:7b` | Ollama 0.40.4. Not used by default: 8 GB RAM limits it to ~7B models |
| Rust toolchain | `nightly-2025-05-13`: rustc 1.89.0-nightly (8405332bd 2025-05-12), cargo 1.89.0-nightly (056f5f4f3 2025-05-09) | Same toolchain as grading |
| Linter | Clippy 0.1.88 (8405332bdf 2025-05-12), categories correctness / style / complexity / perf | |
| Safety analysis | **NewMetrics**, the instructional team's unsafe-metrics tool (`Intelligent-CAT-Lab/CS598JBR-Team-0`, `MP4/newmetrics`, commit `4597e75`), run through `src/newmetrics/run_newmetrics.sh`. If NewMetrics is not installed, the built-in approximate scanner `src/unsafe_metrics.py` is used | `cargo newmetrics \| python3 aggregate.py` |
| Benchmark | CRUST-Bench (`github.com/anirudhkhatry/CRUST-bench`, `datasets/CRUST_bench.zip`) | C from `CBench/`, Rust spec from `RBench/` |

A **single agent** runs with **one active model** at a time. The cascade can move a
run to the next model when a quota runs out, so one run may span several models.
Each saved request in the trajectories records which model served it. The final
translations were produced by `gemini-4-hydrogen` (20 calls) and `gemini-3.6-flash`
(3 calls) for expr, and by `gemini-3-flash-preview` (18 calls) and `gemini-3.6-flash`
(2 calls) for rbtree-lab.

All six Gemini models passed `python3 src/check_setup.py --provider gemini --all-models`
(a real function-calling request) on 2026-11-13. The exception was `gemini-3.8-flash`,
which returned transient 503 "high demand" errors that day.

### Inference settings (`configs/pipeline.toml [inference]`)

| Setting | Value |
|---|---|
| temperature | 0.2 |
| top_p | 0.95 |
| max_tokens per response | 32768 (Gemini counts thinking tokens here, and a whole module can be ~15K tokens) |
| seed | 598, sent where supported (Gemini's endpoint rejects `seed`) |
| tool_choice / parallel tool calls | `auto` / disabled |
| request timeout | 300 s |
| model calls per agent iteration | ≤ 25 |
| tool output shown to the model | truncated to 12,000 chars (head and tail kept) |
| context management | above ~90K estimated tokens, old tool outputs and file bodies are elided (except in the 8 most recent messages) |

### OS / runtime

- macOS 14.5 (23F79), Apple M3 (arm64), 8 GB RAM
- Python 3.13.1 (3.11+ required for `tomllib`)
- rustup with `nightly-2025-05-13`, plus `clippy` and `rustfmt` (and `rustc-dev` and `llvm-tools-preview` for NewMetrics)
- Ollama 0.40.4 (optional)

### Tools available to the agent (`configs/tools.json`)

The agent works in a sandboxed view: `c/` is the original C project (read-only) and
`rust/` is the crate being written. It has **no arbitrary shell**.

| Tool | Purpose |
|---|---|
| `list_files`, `read_file`, `search` | inspect the C project, the Rust interface, and the tests |
| `write_file`, `replace_in_file` | modify Rust code. Only `.rs` files under `rust/src/` can be written. `src/bin/*` (tests), `src/interfaces/*` (spec copy), `Cargo.toml` and `Cargo.lock` are protected |
| `cargo` (`check` \| `build` \| `test` \| `clippy`) | always `cargo +nightly-2025-05-13 …`. `check`/`build` also report interface conformance. `clippy` uses the graders' 4 categories and reports per-category counts |
| `unsafe_metrics` | unsafe lines / calls / casts / pointer arithmetic (+ extra metrics), via `[unsafe_metrics].command` |
| `finish` | ends the iteration; the controller then evaluates independently |

### API / usage limits affecting the experiment

- **Gemini free tier.** Quotas apply per model and per Google Cloud project (not per
  key). Requests-per-day resets at midnight Pacific. TPM counts input tokens. The
  values below were read from our project's AI Studio rate-limit page on 2026-11-13:

  | Model | RPM | TPM | RPD | Used? |
  |---|---|---|---|---|
  | `gemini-4-hydrogen` | 5 | 250K | 20 | yes |
  | `gemini-3.8-flash` | 5 | 250K | 20 | yes (often 503 "high demand" or hung) |
  | `gemini-3.6-flash` | 5 | 250K | 20 | yes |
  | `gemini-3-flash-preview` | 5 | 250K | 20 | yes |
  | `gemini-3.5-flash-lite` | 15 | 250K | 500 | yes |
  | `gemini-3.1-flash-lite` | 15 | 250K | 500 | yes |
  | Gemma 4 26B / 31B | 30 | **16K** | 14.4K | no: 16K input tokens/min is too small for C source plus conversation context |
  | Gemini 2.5 Flash / Flash-Lite | 5 / 10 | 250K | 20 | no: deprecated |
  | Gemini 3.1 Pro, Gemini 4 Carbon / Argon | 0 | 0 | 0 | no: not available on the free tier |

  - At most 80 requests/day therefore go to the stronger Flash models, and up to 1,000
    more to Flash-Lite.
  - The pipeline throttles to 4 / 12 RPM, one to three below Google's limits, because
    failed requests also count.
  - A local per-model request ledger (`.cache/quota_usage.json`, git-ignored) lets the
    controller skip exhausted models instead of wasting requests on 429s.
  - Free-tier prompts may be used by Google to improve its products. The inputs here
    are only public benchmark code.
- **OpenRouter free variants** (docs, Nov 2026): **20 requests/min**, and
  **50 requests/day** for accounts with fewer than 10 purchased credits (we bought
  none). The pipeline throttles to 18 req/min and caps a run at 45 requests.
- **Effect on the experiment.** The strong models' daily quota was the binding
  constraint. On 2026-11-13 it ran out before expr could be solved. The weaker
  remaining models (Flash-Lite, Nemotron Ultra) could not pass the expr tests (runs
  2–4 in `previous_runs/`). The successful run happened after the quota reset on
  2026-11-14.
- **Fallback.** If a provider's free quota runs out mid-run, the controller switches
  to the next provider in `provider_fallbacks` or checkpoints and stops. Either way,
  the switch is logged in the trajectory.

## Setup

```bash
# 1. Rust toolchain used for translation, repair and grading
rustup toolchain install nightly-2025-05-13 --component clippy,rustfmt

# 2. Python 3.11+ (no third-party packages: requirements.txt is stdlib only)
python3 --version

# 3. Course unsafe-metrics tool (NewMetrics), from the course repository
git clone https://github.com/Intelligent-CAT-Lab/CS598JBR-Team-0.git
rustup component add rustc-dev llvm-tools-preview --toolchain nightly-2025-05-13
(cd CS598JBR-Team-0/MP4/newmetrics && cargo install --debug --locked --path . --force)
#    The wrapper MP4/src/newmetrics/run_newmetrics.sh uses an unmodified copy of the
#    course's aggregate.py, so no extra path setup is needed.

# 4. Free API keys (never commit them; configs/.env is git-ignored)
#    Gemini:     https://aistudio.google.com/apikey   (primary)
#    OpenRouter: https://openrouter.ai/keys           (secondary)
cp MP4/configs/.env.example MP4/configs/.env    # fill in GEMINI_API_KEY / OPENROUTER_API_KEY

# 5. (optional) local model
ollama pull qwen2.5-coder:7b

# 6. Verify everything: toolchain, NewMetrics, configs, specs compile, keys + tool calling
cd MP4 && python3 src/check_setup.py
python3 src/check_setup.py --provider gemini --all-models   # probe every model (1 request each)
```

## Run

One command reproduces everything for a project: environment check, the agentic
loop, then a grader-style build / test / clippy / unsafe evaluation.

```bash
bash MP4/src/reproduce.sh project_1 --fresh     # expr
bash MP4/src/reproduce.sh project_2 --fresh     # rbtree-lab
```

Or call the controller directly (from `MP4/`):

```bash
python3 src/run_pipeline.py --project project_1            # start, or resume a paused run
python3 src/run_pipeline.py --project project_1 --fresh    # archive the previous run and restart
python3 src/run_pipeline.py --project project_1 --provider openrouter --max-iterations 4
python3 src/run_pipeline.py --project project_1 --evaluate-only
python3 src/run_pipeline.py --project project_1 --refresh-summary   # re-evaluate + rewrite summaries, no model calls
bash src/newmetrics/run_newmetrics.sh translations/project_1 summary.json   # NewMetrics only
```

The same code runs both projects. Project-specific input comes only from
`configs/projects.toml` (paths, module names, test files). The C sources, interface,
tests and the required-public-API checklist are inlined into the prompts
automatically.

If the free quota runs out mid-run, the controller evaluates the crate, saves
`state.json` with status `paused_quota`, and exits. Re-running the same command
resumes at the next iteration.

## Pipeline

```
            ┌──────────── controller (src/, configs/pipeline.toml) ─────────────┐
 setup:     copy benchmark spec → translations/project_N, interfaces/<m>.rs → src/<m>.rs
            │                                                                   │
 iter k:    prompt = system.md + (translate.md if k=1 else repair.md+feedback)  │
            │        + inlined C/interface/tests + required-API checklist      │
            ▼                                                                   │
     ┌─ agent session (≤25 model calls) ──────────────────────────┐             │
     │ read C / interface / tests → write Rust → cargo check/test │             │
     │ → clippy → unsafe_metrics → repair … → finish              │             │
     └────────────────────────────────────────────────────────────┘             │
            ▼                                                                   │
 evaluate:  integrity guard (tests, spec, Cargo files unchanged; pub signatures │
            kept; no FFI; no test literals copied) → cargo build → cargo test → │
            clippy (4 categories) → unsafe metrics → score; save feedback, diff │
            ▼                                                                   │
 stop? ── no ──► keep best snapshot (revert regressions), next repair prompt ───┘
   │yes
   ▼
 final crate in translations/project_N, summary.json in trajectories/project_N
```

**Feedback path.** Inside a session, the agent sees the raw (truncated) compiler,
test, Clippy and unsafe-metrics output as tool results. Between sessions, the
controller re-runs everything itself and writes a structured report into
`prompts/repair.md`: status table, compile errors, failing tests with assertion
messages, Clippy warnings per category, unsafe locations, and integrity violations.

**Score.** Used for the best snapshot and for measuring progress, and compared
lexicographically among real translations (the untouched skeleton is only a
reference): builds → tests passed → −(integrity violations) → −(primary unsafe
total) → −(Clippy total in `src/`).
- Integrity violations block success and appear first in the repair feedback.
- They lower the score without discarding an otherwise working translation.
- A tampered test file is restored before testing, so it can never be what makes
  tests pass.

### Stopping condition

After each iteration, the run stops at the first of these that is true:

1. **Success:** integrity checks pass, `cargo build` succeeds, all tests pass, all
   four primary unsafe metrics are 0, and the Clippy total in `src/` is 0.
2. **Iteration cap:** 6 outer iterations (`max_iterations`).
3. **No progress:** the score has not improved for 3 consecutive iterations (`no_progress_patience`).
4. **Request budget:** the provider's `max_requests_per_run` is used up (Gemini 300
   across all its models; OpenRouter 45, which keeps it under its free daily cap), or
   every configured model is out of daily quota. The run checkpoints, and re-running
   the same command resumes it.

The final translation is the best-scoring snapshot, not necessarily the last one.

## Outputs

```
MP4/
├── README.md
├── PROGRESS_REPORT_MP4.tex / .md   # Task 4 report section (LaTeX for Overleaf, Markdown copy)
├── requirements.txt     # stdlib only (nothing to pip install)
├── src/
│   ├── run_pipeline.py  # controller: setup → agent iterations → evaluation → stop (entry point)
│   ├── reproduce.sh     # one-command reproduction for a project (check + pipeline + grader eval)
│   ├── llm.py           # OpenAI-compatible client, quota-aware model cascade, rate limiting
│   ├── agent_tools.py   # sandboxed tool implementations (file, cargo, unsafe_metrics, finish)
│   ├── evaluate.py      # integrity guard, build, tests, clippy per category, score, feedback text
│   ├── unsafe_metrics.py# runs the configured unsafe-metrics tool; built-in approximate scanner as fallback
│   ├── newmetrics/      # run_newmetrics.sh + unmodified copy of the course's aggregate.py
│   ├── trajectory.py    # redacting JSONL/JSON/Markdown trajectory writer
│   ├── common.py        # config/env loading, secret redaction, subprocess helpers
│   └── check_setup.py   # verifies toolchain, NewMetrics, configs, spec builds, API keys + tool calling
├── configs/
│   ├── pipeline.toml    # providers/models, inference settings, agent loop, stopping condition,
│   │                    # evaluation commands, unsafe-metrics command, integrity guards, log redaction
│   ├── projects.toml    # per-project paths/metadata (no per-function hints)
│   ├── tools.json       # function-calling schemas of the tools exposed to the agent
│   ├── prompts/         # system.md, translate.md (iteration 1), repair.md (iterations 2..N)
│   └── .env.example     # names of required env vars (real configs/.env is git-ignored)
├── benchmark/RBench/    # (addition) unmodified CRUST-Bench Rust interfaces + tests
├── subjects/            # original C projects: project_1 = expr, project_2 = rbtree-lab
├── translations/        # final generated Rust crates (project_1/, project_2/)
└── trajectories/        # per-project execution logs (project_1/, project_2/)
```

**Translations.** `translations/project_N/` is a complete CRUST-Bench crate, built
and tested with no extra steps. The agent wrote only `src/<module>.rs` and added
`#![forbid(unsafe_code)]` to `src/lib.rs`. The benchmark tests, interface copy,
`Cargo.toml` and `Cargo.lock` are byte-identical to CRUST-Bench.

### Trajectory format (`trajectories/project_N/`)

| File | Contents |
|---|---|
| `TRAJECTORY.md` | human-readable summary: per-iteration score, agent turns, revert decisions, final evaluation |
| `events.jsonl` | every event in order: prompts, each model response (serving model, token usage, text, tool calls), each tool call with arguments and (truncated) result, API errors/retries, quota waits, iteration ends |
| `iter_NN/prompt.md` | exact user prompt of iteration N (translate, or repair + feedback) |
| `iter_NN/session_messages.json` | full message list of the agent session (system, user, assistant, tool) |
| `iter_NN/feedback.{json,md}` | controller evaluation after iteration N: integrity, build diagnostics, test results and failure messages, Clippy per category, unsafe metrics |
| `iter_NN/diff.patch`, `iter_NN/snapshot/` | what the agent changed in iteration N, and the resulting sources |
| `iter_00/` | baseline evaluation of the untouched interface skeleton |
| `final_evaluation.{json,md}`, `summary.json`, `state.json` | final status, best iteration, metrics, request counts per model |
| `newmetrics_raw.log`, `newmetrics_summary.json` | NewMetrics output for the final crate (`cargo newmetrics \| aggregate.py`) |
| `previous_runs/run_<start>/` | earlier runs of the same project, kept for transparency (`--fresh` archives instead of deleting) |

API keys are redacted from every log before it is written.

## Evaluation

Final results, graders' commands, `nightly-2025-05-13`:

| Project | Compiles | Tests passed / total | Agent iterations | Model calls |
|---|---|---|---|---|
| expr | yes | 2 / 2 | 2 | 23 |
| rbtree-lab | yes | 6 / 6 | 1 | 20 |

Safety, from the course **NewMetrics** tool (`trajectories/project_N/newmetrics_summary.json`):

| Project | Unsafe lines | Unsafe calls | Unsafe casts | Pointer arithmetic | Raw-ptr derefs | Raw-ptr decls | Total spans |
|---|---|---|---|---|---|---|---|
| expr | 0 | 0 | 0 | 0 | 0 | 0 | 42,047 |
| rbtree-lab | 0 | 0 | 0 | 0 | 0 | 0 | 21,306 |

Both crates compile with `#![forbid(unsafe_code)]`. As a sanity check, the same tool
reported 5 unsafe lines, 2 unsafe calls, 1 unsafe cast and 2 pointer-arithmetic
operations on a small deliberately unsafe crate.

Clippy (`--all-targets --all-features -- -W clippy::correctness -W clippy::style -W clippy::complexity -W clippy::perf`):

| Project | Correctness | Style | Complexity | Perf | Where |
|---|---|---|---|---|---|
| expr | 0 | 3 | 1 | 0 | all 4 are in the unmodified benchmark file `src/bin/test.rs`; 0 in the translation |
| rbtree-lab | 0 | 0 | 0 | 0 | |

To evaluate a translation by hand:

```bash
cd MP4/translations/project_1
cargo +nightly-2025-05-13 build
cargo +nightly-2025-05-13 test
cargo +nightly-2025-05-13 clippy --all-targets --all-features -- \
    -W clippy::correctness -W clippy::style -W clippy::complexity -W clippy::perf
bash ../../src/newmetrics/run_newmetrics.sh . summary.json
```

## Manual interventions log

The handout requires documenting every manual intervention. No translated Rust code
was ever edited by hand: all program logic in `translations/` was written by the
agent.

| Date | What changed | Why | Program logic affected? |
|---|---|---|---|
| 2026-11-13 | Controller fix in `src/evaluate.py`: the public-signature check now ignores `mut` in parameter patterns (`mut self` ≡ `self`) | The first project_2 run produced a correct translation (6/6 tests, 0 Clippy, 0 unsafe), but the check flagged `pub fn delete_rbtree(mut self)` as an interface change, and the controller reverted to the skeleton. The run was stopped and rerun with `--fresh`; the first run is archived in `trajectories/project_2/previous_runs/` | No. Only the pipeline's checker changed |
| 2026-11-13 | Controller fixes after the first project_1 run: (a) the signature check ignores lifetime annotations that elision infers (`fn f<'a>(x: &'a T)` ≡ `fn f(x: &T)`); (b) integrity violations became their own score term instead of counting as "does not build"; (c) per-minute limits set below Google's (4 / 12 RPM), because failed requests also count | Run 1 flagged an elided lifetime as an interface change and reverted a 1/2-tests translation to the empty skeleton. Run 1 is archived in `trajectories/project_1/previous_runs/`, and the project was rerun with `--fresh` | No. Only the controller changed |
| 2026-11-13 | Pipeline improvements after project_1 runs 2–3: (a) the prompts carry an auto-extracted **required public API checklist** from the interface file; (b) the agent's `cargo check/build` tool also reports interface violations; (c) the controller never reverts to the untouched skeleton (iteration 0), only to an earlier real translation; (d) repair prompts inline the C sources as well as the current Rust; (e) `--provider` overrides still fall back to the default provider | Every model dropped interface items the tests do not use (`ExprNode::new`, `expr_free`, `state_t`). Run 3 (OpenRouter) was reverted to the skeleton after iteration 1, and was stopped by hand during iteration 2 to save quota. Runs 2–3 are archived in `trajectories/project_1/previous_runs/` | No. Only prompts and controller changed; nothing is project-specific |
| 2026-11-13 | The untouched skeleton (iteration 0) no longer competes for "best": the first real translation always becomes the best snapshot, and later regressions revert to the best translation | In run 4 the skeleton (builds, 0 tests, 0 violations) outscored real translations that built but failed tests. The run would have ended on the skeleton, and a non-building iteration could not be reverted | No. Controller only |
| 2026-11-14 | `src/llm.py`: a timed-out or dropped connection is no longer retried on the same model; the model is benched for 30 min and the cascade moves on | `gemini-3.8-flash` repeatedly hung until the 300 s timeout, and each hang was retried 3×. The project_2 rerun on the final pipeline was stopped by hand mid-iteration and restarted with `--fresh`; the stopped run is archived in `trajectories/project_2/previous_runs/` | No. Controller only |
| 2026-11-14 | Switched `[unsafe_metrics].command` to the course NewMetrics tool (released after our runs started), added `src/newmetrics/`, and re-ran the final evaluation of both crates with `--refresh-summary` (no model calls) | During the final runs, the agent's `unsafe_metrics` tool used our built-in scanner, which reported 0 for both crates. NewMetrics confirms 0 on all metrics | No. Evaluation only |

## Credentials

No keys are stored in the repository. `configs/.env` is git-ignored. Every
trajectory is scrubbed of the `GEMINI_API_KEY` / `OPENROUTER_API_KEY` values and of
key-shaped patterns (`AIza…`, `sk-or-…`, `Bearer …`) before it is saved.
