#!/usr/bin/env python3
"""crust-agent: iterative agentic C -> Rust translation pipeline (MP4, Group 10).

Cycle per iteration:
  prompt (translate | repair + feedback) -> agent session with tools
  (read C / interface / tests, write Rust, cargo check/build/test/clippy,
  unsafe_metrics, ... finish) -> independent evaluation (integrity, build,
  tests, clippy x4 categories, unsafe metrics) -> score -> stop or repair.

Usage (from MP4/):
  python3 src/run_pipeline.py --project project_1            # start or resume
  python3 src/run_pipeline.py --project project_2 --fresh    # wipe and restart
  python3 src/run_pipeline.py --project project_1 --provider openrouter
  python3 src/run_pipeline.py --project project_1 --evaluate-only
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_tools import ToolExecutor, Workspace          # noqa: E402
from common import (MP4, Redactor, estimate_tokens, fill_template, load_config,  # noqa: E402
                    load_env_file, now_iso, truncate)
from evaluate import Evaluator, feedback_sections, report_markdown  # noqa: E402
from llm import LLMError, ModelPool, QuotaExhausted     # noqa: E402
from trajectory import Trajectory                       # noqa: E402


# ------------------------------------------------------------------ setup
def setup_crate(spec: Path, crate: Path, modules: list[str]) -> None:
    """Copy the CRUST-Bench spec and place each interface at src/<module>.rs."""
    if crate.exists():
        shutil.rmtree(crate)
    shutil.copytree(spec, crate, ignore=shutil.ignore_patterns("target", ".git"))
    for m in modules:
        shutil.copy2(crate / "src/interfaces" / f"{m}.rs", crate / "src" / f"{m}.rs")


def archive_previous_run(traj_dir: Path) -> None:
    """--fresh keeps earlier runs (moved to previous_runs/<start time>/) instead of deleting them."""
    entries = [p for p in traj_dir.iterdir() if p.name not in ("previous_runs", ".gitkeep")]
    if not entries:
        return
    try:
        started = json.loads((traj_dir / "state.json").read_text())["started"]
    except (OSError, ValueError, KeyError):
        started = now_iso()
    dest = traj_dir / "previous_runs" / ("run_" + started.replace(":", "").replace("-", "")[:15])
    dest.mkdir(parents=True, exist_ok=True)
    for p in entries:
        shutil.move(str(p), dest / p.name)


def own_sources(crate: Path) -> dict[str, str]:
    return {f.relative_to(crate).as_posix(): f.read_text()
            for f in sorted((crate / "src").rglob("*.rs"))
            if not f.relative_to(crate).as_posix().startswith(("src/bin/", "src/interfaces/"))}


def snapshot(crate: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    for rel, text in own_sources(crate).items():
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_text(text)


def restore(snap: Path, crate: Path) -> None:
    for rel in own_sources(crate):                 # drop files the agent added since
        (crate / rel).unlink()
    for f in snap.rglob("*.rs"):
        rel = f.relative_to(snap)
        (crate / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, crate / rel)


def diff_text(before: dict[str, str], after: dict[str, str]) -> str:
    out = []
    for rel in sorted(set(before) | set(after)):
        a, b = before.get(rel, ""), after.get(rel, "")
        if a != b:
            out += difflib.unified_diff(a.splitlines(True), b.splitlines(True), f"a/{rel}", f"b/{rel}")
    return "".join(out)


def score_text(s: list) -> str:
    if len(s) == 4:                     # runs recorded before integrity became its own score term
        s = [s[0], s[1], 0, s[2], s[3]]
    return (f"builds={s[0]} tests_passed={s[1]} integrity_violations={-s[2]} unsafe={-s[3]} "
            f"clippy_src={-s[4] if s[4] > -10**6 else 'n/a'}")


# ------------------------------------------------------------------ prompts
def read_cfg_file(rel: str) -> str:
    return (MP4 / rel).read_text()


def inline_files(paths: list[tuple[str, Path]], max_chars: int) -> str:
    chunks, used = [], 0
    for label, p in paths:
        text = p.read_text(errors="replace")
        if used + len(text) > max_chars:
            chunks.append(f"### {label}\n(omitted for length - use read_file)")
            continue
        used += len(text)
        lang = "rust" if p.suffix == ".rs" else "c"
        chunks.append(f"### {label}\n```{lang}\n{text}\n```")
    return "\n\n".join(chunks)


def translate_prompt(cfg, proj, k, max_iter) -> str:
    c_dir, spec = MP4 / proj["c_dir"], MP4 / proj["rust_spec_dir"]
    ctx = ""
    if cfg["agent"]["inline_context"]:
        files = [(f"c/{s}", c_dir / s) for s in proj["c_sources"]]
        files += [(f"rust/src/{m}.rs (interface to implement)", spec / "src/interfaces" / f"{m}.rs")
                  for m in proj["modules"]]
        files += [(f"rust/{t} (read-only tests)", spec / t) for t in proj["test_files"]]
        files += [("rust/src/lib.rs", spec / "src/lib.rs"), ("rust/Cargo.toml", spec / "Cargo.toml")]
        ctx = ("## Project context (supplied automatically)\n\n"
               + inline_files(files, cfg["agent"]["inline_context_max_chars"]))
    return fill_template(read_cfg_file(cfg["agent"]["translate_prompt"]), {
        "iteration": k, "max_iterations": max_iter, "project_name": proj["name"],
        "crate_name": proj["crate_name"],
        "c_files": "\n".join(f"- c/{s}" for s in proj["c_sources"]),
        "modules": "\n".join(f"- `{m}` -> rust/src/{m}.rs" for m in proj["modules"]),
        "test_files": "\n".join(f"- rust/{t}" for t in proj["test_files"]),
        "inlined_context": ctx,
    })


def repair_prompt(cfg, proj, k, max_iter, report, regression_note, crate) -> str:
    vals = feedback_sections(report, cfg["agent"]["tool_output_char_limit"])
    current = ""
    if cfg["agent"]["inline_context"]:
        files = [(f"rust/{rel}", crate / rel) for rel in own_sources(crate)]
        current = "## Current Rust sources (supplied automatically)\n\n" + inline_files(
            files, cfg["agent"]["inline_context_max_chars"])
    vals.update({"iteration": k, "max_iterations": max_iter, "project_name": proj["name"],
                 "regression_note": regression_note, "current_rust": current})
    return fill_template(read_cfg_file(cfg["agent"]["repair_prompt"]), vals)


# ------------------------------------------------------------------ agent session
def compact(messages: list, budget_tokens: int, keep_recent: int) -> int:
    """Shrink old tool outputs / file-write arguments when the context grows too large."""
    if estimate_tokens(messages) <= budget_tokens:
        return 0
    shrunk = 0
    for m in messages[2:-keep_recent]:
        if m["role"] == "tool" and len(m.get("content", "")) > 600:
            m["content"] = m["content"][:300] + "\n...[older tool output elided to save context; re-run if needed]"
            shrunk += 1
        for tc in m.get("tool_calls") or []:
            args = tc["function"].get("arguments", "")
            if len(args) > 600:
                try:
                    a = json.loads(args)
                    for key in ("content", "new_text", "old_text"):
                        if isinstance(a.get(key), str) and len(a[key]) > 300:
                            a[key] = f"<{len(a[key])} chars elided; read the file for its current content>"
                    tc["function"]["arguments"] = json.dumps(a)
                    shrunk += 1
                except ValueError:
                    pass
    return shrunk


def run_session(cfg, pool: ModelPool, tools: ToolExecutor, traj: Trajectory, system: str, prompt: str) -> dict:
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    max_turns = cfg["agent"]["max_tool_turns_per_iteration"]
    traj.event("prompt", role="user", content=prompt)
    summary, finished, nudges, turns, paused = "", False, 0, 0, False
    for turn in range(1, max_turns + 1):
        turns = turn
        n = compact(messages, cfg["agent"]["context_token_budget"], cfg["agent"]["keep_recent_messages"])
        if n:
            traj.event("context_compacted", items=n)
        try:
            msg, meta = pool.chat(messages, cfg["tools"])
        except QuotaExhausted as e:
            traj.event("quota_exhausted", detail=str(e))
            paused = True
            break
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        traj.event("llm_response", turn=turn, **meta, content=msg.get("content"),
                   reasoning=msg.get("reasoning") or msg.get("reasoning_content"),
                   tool_calls=[{"name": c["function"]["name"], "arguments": c["function"].get("arguments")}
                               for c in calls])
        if not calls:
            nudges += 1
            if nudges > 2:
                break
            messages.append({"role": "user", "content": "Continue working with the tools. Base your next step on "
                             "cargo/test/clippy/unsafe_metrics output, and call `finish` when done."})
            continue
        remaining = max_turns - turn
        for c in calls:
            name = c["function"]["name"]
            try:
                args = json.loads(c["function"].get("arguments") or "{}")
                if not isinstance(args, dict):
                    raise ValueError("arguments must be a JSON object")
                result, info = tools.execute(name, args)
            except ValueError as e:
                result, info = f"ERROR: could not parse tool arguments as JSON: {e}", {"ok": False}
            if remaining <= 3 and name != "finish":
                result += f"\n[controller: {remaining} model turn(s) left in this iteration - call finish soon]"
            messages.append({"role": "tool", "tool_call_id": c.get("id", name), "content": result})
            traj.event("tool_call", turn=turn, tool=name, arguments=args if name != "write_file" else
                       {"path": args.get("path"), "content": args.get("content")},
                       result=truncate(result, 6000), info=info)
            if info.get("finished"):
                finished, summary = True, info.get("summary", "")
        if finished:
            break
    return {"messages": messages, "turns": turns, "finished": finished, "summary": summary, "paused": paused,
            "files_read": sorted(tools.files_read), "files_written": sorted(tools.files_written)}


# ------------------------------------------------------------------ main loop
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, help="project_1 or project_2 (see configs/projects.toml)")
    ap.add_argument("--provider", choices=["gemini", "openrouter", "ollama"], help="override [model].provider")
    ap.add_argument("--max-iterations", type=int, help="override [stopping].max_iterations")
    ap.add_argument("--fresh", action="store_true", help="discard previous translation/trajectory and restart")
    ap.add_argument("--evaluate-only", action="store_true", help="only evaluate the current translation")
    ap.add_argument("--refresh-summary", action="store_true",
                    help="re-run the final evaluation and rewrite summary files of a finished run (no model calls)")
    args = ap.parse_args()

    load_env_file()
    cfg = load_config()
    if args.project not in cfg["projects"]:
        ap.error(f"unknown project {args.project}; choose from {list(cfg['projects'])}")
    proj = cfg["projects"][args.project]
    stop = cfg["stopping"]
    max_iter = args.max_iterations or stop["max_iterations"]
    crate, spec = MP4 / proj["output_dir"], MP4 / proj["rust_spec_dir"]
    traj_dir = MP4 / proj["trajectory_dir"]
    redactor = Redactor(cfg)

    if args.fresh and traj_dir.exists():
        archive_previous_run(traj_dir)
    traj = Trajectory(traj_dir, redactor)
    state_path = traj_dir / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    evaluator = Evaluator(cfg, proj, crate, spec)

    if args.evaluate_only:
        rep = evaluator.full()
        print(report_markdown(rep))
        return 0 if rep["success"] else 1

    if args.refresh_summary:
        if not state:
            ap.error("no run to summarize")
        finalize(cfg, proj, state, crate, traj, evaluator)
        return 0

    if state and state["status"] in ("success", "max_iterations", "no_progress", "run_budget"):
        print(f"{args.project} already finished with status '{state['status']}'. Use --fresh to rerun.")
        return 0

    if state is None:
        setup_crate(spec, crate, proj["modules"])
        traj.write_json("run_config.json", {k: v for k, v in cfg.items() if k != "tools"} | {
            "project_id": args.project, "max_iterations": max_iter, "provider_override": args.provider})
        traj.write_json("tools.json", cfg["tools"])
        base = evaluator.full()
        snapshot(crate, traj_dir / "iter_00/snapshot")
        traj.write_json("iter_00/feedback.json", base)
        traj.write_text("iter_00/feedback.md", report_markdown(base))
        state = {"project": args.project, "name": proj["name"], "started": now_iso(), "iteration": 0,
                 "best_iteration": 0, "best_score": base["score"], "no_progress": 0, "status": "running",
                 "history": [{"iteration": 0, "score": base["score"], "note": "skeleton baseline"}],
                 "runs": [], "requests": {}, "models_used": {}}
        traj.event("run_start", project=args.project, name=proj["name"], baseline=score_text(base["score"]))
    else:
        traj.event("run_resume", from_iteration=state["iteration"], status=state["status"])
    state["runs"].append({"started": now_iso(), "provider": args.provider or cfg["model"]["provider"]})
    state["status"] = "running"
    state_path.write_text(json.dumps(state, indent=2))

    try:
        pool = ModelPool(cfg, traj, args.provider)
    except LLMError as e:
        print(f"ERROR: {e}")
        return 2
    system = read_cfg_file(cfg["agent"]["system_prompt"])
    ws = Workspace(MP4 / proj["c_dir"], crate, cfg["integrity"]["protected_globs"])
    # Feedback for the code currently in the crate (the best snapshot if the last iteration was reverted).
    last = state["history"][-1]
    shown = last.get("reverted_to", state["iteration"])
    last_report = json.loads((traj_dir / f"iter_{shown:02d}/feedback.json").read_text())
    regression_note = state.get("pending_regression_note", "")

    while state["iteration"] < max_iter:
        k = state["iteration"] + 1
        traj.iteration = k
        before = own_sources(crate)
        if k == 1:
            prompt = translate_prompt(cfg, proj, k, max_iter)
        else:
            prompt = repair_prompt(cfg, proj, k, max_iter, last_report, regression_note, crate)
        traj.write_text(f"iter_{k:02d}/prompt.md", prompt)
        traj.event("iteration_start", prompt_kind="translate" if k == 1 else "repair")
        print(f"[{args.project}] iteration {k}/{max_iter} ...", flush=True)

        tools = ToolExecutor(ws, evaluator, cfg)
        t0 = time.time()
        session = run_session(cfg, pool, tools, traj, system, prompt)
        traj.write_json(f"iter_{k:02d}/session_messages.json", session["messages"])

        report = evaluator.full()
        after = own_sources(crate)
        traj.write_json(f"iter_{k:02d}/feedback.json", report)
        traj.write_text(f"iter_{k:02d}/feedback.md", report_markdown(report))
        traj.write_text(f"iter_{k:02d}/diff.patch", diff_text(before, after))
        snapshot(crate, traj_dir / f"iter_{k:02d}/snapshot")

        improved = report["score"] > state["best_score"]
        entry = {"iteration": k, "score": report["score"], "turns": session["turns"],
                 "finished_by_agent": session["finished"], "agent_summary": session["summary"],
                 "files_read": session["files_read"], "files_written": session["files_written"],
                 "seconds": round(time.time() - t0), "improved": improved, "success": report["success"],
                 "paused_for_quota": session["paused"]}
        regression_note = ""
        if improved:
            state["best_score"], state["best_iteration"], state["no_progress"] = report["score"], k, 0
        else:
            state["no_progress"] += 1
            if report["score"] < state["best_score"] and cfg["agent"]["keep_best_snapshot"]:
                restore(traj_dir / f"iter_{state['best_iteration']:02d}/snapshot", crate)
                regression_note = (f"**Note:** iteration {k} scored worse ({score_text(report['score'])}) than "
                                   f"iteration {state['best_iteration']} ({score_text(state['best_score'])}). "
                                   f"The controller reverted the code to iteration {state['best_iteration']}; the "
                                   "feedback below is for that restored version.")
                report = json.loads((traj_dir / f"iter_{state['best_iteration']:02d}/feedback.json").read_text())
                entry["reverted_to"] = state["best_iteration"]
        last_report = report
        state["history"].append(entry)
        state["iteration"] = k
        state["requests"] = dict(pool.run_requests)
        for kk, v in pool.ledger["counts"].items():
            state["models_used"][kk] = v
        state["pending_regression_note"] = regression_note
        traj.event("iteration_end", score=score_text(entry["score"]), improved=improved, success=report["success"],
                   reverted_to=entry.get("reverted_to"))
        print(f"[{args.project}] iteration {k}: {score_text(entry['score'])}"
              + (" (improved)" if improved else "") + (" -> reverted" if "reverted_to" in entry else ""), flush=True)

        if report["success"] and stop["stop_on_success"]:
            state["status"] = "success"
        elif state["no_progress"] >= stop["no_progress_patience"] and not session["paused"]:
            state["status"] = "no_progress"
        elif session["paused"] or not pool.budget_left():
            state["status"] = "paused_quota"
        state_path.write_text(json.dumps(state, indent=2))
        if state["status"] != "running":
            break
    else:
        state["status"] = "max_iterations"

    finalize(cfg, proj, state, crate, traj, evaluator)
    state_path.write_text(json.dumps(state, indent=2))
    print(f"[{args.project}] stopped: {state['status']} (best iteration {state['best_iteration']}: "
          f"{score_text(state['best_score'])})")
    return 0


def finalize(cfg, proj, state, crate, traj, evaluator) -> None:
    """Make sure the crate holds the best snapshot and write summary files."""
    traj_dir = traj.root
    best = state["best_iteration"]
    if best > 0:
        restore(traj_dir / f"iter_{best:02d}/snapshot", crate)
    final = evaluator.full()
    traj.iteration = state["iteration"]
    traj.write_json("final_evaluation.json", final)
    traj.write_text("final_evaluation.md", report_markdown(final))
    clippy = final["clippy"] or {}
    summary = {
        "project": state["project"], "name": proj["name"], "status": state["status"],
        "iterations": state["iteration"], "best_iteration": best,
        "compiles": final["build"]["ok"], "tests_passed": final["tests"]["passed"],
        "tests_total": final["tests"]["total"],
        "pass_rate": round(final["tests"]["passed"] / max(1, final["tests"]["total"]), 3),
        "integrity_ok": final["integrity"]["ok"],
        "clippy_src": {k: v["src"] for k, v in clippy.get("categories", {}).items()},
        "clippy_tests_readonly": {k: v["tests"] for k, v in clippy.get("categories", {}).items()},
        "clippy_grader_command": clippy.get("grader_command"),
        "unsafe": final["unsafe"]["metrics"], "unsafe_tool": final["unsafe"]["tool"],
        "model_requests_by_provider": state["requests"], "model_requests_today_by_model": state["models_used"],
        "history": state["history"], "finished_at": now_iso(),
    }
    traj.write_json("summary.json", summary)
    rows = ["| Iter | Score (builds, tests, integrity, unsafe, clippy) | Turns | Improved | Reverted | Agent summary |",
            "|---|---|---|---|---|---|"]
    for h in state["history"]:
        rows.append(f"| {h['iteration']} | {score_text(h['score'])} | {h.get('turns', '-')} | {h.get('improved', '-')} "
                    f"| {h.get('reverted_to', '')} | {' '.join((h.get('agent_summary') or h.get('note', '')).split())[:200]} |")
    traj.write_text("TRAJECTORY.md", f"# Trajectory: {proj['name']} ({state['project']})\n\n"
                    f"Status: **{state['status']}**; best iteration {best}.\n\n" + "\n".join(rows)
                    + "\n\n## Final evaluation\n\n" + report_markdown(final)
                    + "\n\nFiles: `events.jsonl` (every model response and tool call), `iter_NN/prompt.md`, "
                      "`iter_NN/session_messages.json`, `iter_NN/feedback.{json,md}`, `iter_NN/diff.patch`, "
                      "`iter_NN/snapshot/`, `summary.json`.\n")
    traj.event("run_end", status=state["status"], best_iteration=best, final=summary)


if __name__ == "__main__":
    sys.exit(main())
