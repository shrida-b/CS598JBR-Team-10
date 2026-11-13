#!/usr/bin/env python3
"""Verify the MP4 environment before running the translation pipeline.

Checks (in order):
  1. Python version (tomllib needs 3.11+)
  2. Pinned Rust toolchain, cargo and clippy
  3. configs/ parse and every referenced path exists
  4. Each CRUST-Bench spec compiles after the standard setup step
     (src/interfaces/<m>.rs -> src/<m>.rs) with the pinned toolchain
  5. Model providers: API key present, /models reachable, and a tiny
     function-calling request returns a tool call (1 request per provider)

Usage (from MP4/):
  python3 src/check_setup.py                 # everything
  python3 src/check_setup.py --no-network    # skip provider checks
  python3 src/check_setup.py --provider gemini
  python3 src/check_setup.py --provider gemini --all-models   # probe every model
Exit code is 0 only if every non-skipped check passes. Keys are never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

MP4 = Path(__file__).resolve().parent.parent
OK, FAIL, SKIP = "\033[32mOK\033[0m", "\033[31mFAIL\033[0m", "\033[33mSKIP\033[0m"
failures: list[str] = []


def report(status: str, name: str, detail: str = "") -> None:
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    if status == FAIL:
        failures.append(name)


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ without overriding existing vars."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


def redact(text: str, cfg: dict) -> str:
    for env in cfg["trajectory"]["redact_env"]:
        if os.environ.get(env):
            text = text.replace(os.environ[env], "<REDACTED>")
    for pat in cfg["trajectory"]["redact_patterns"]:
        text = re.sub(pat, "<REDACTED>", text)
    return text


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------- checks
def check_python() -> None:
    v = sys.version_info
    status = OK if v >= (3, 11) else FAIL
    report(status, "python", f"{v.major}.{v.minor}.{v.micro} (need >= 3.11)")


def check_toolchain(toolchain: str) -> None:
    for tool in (["rustc", f"+{toolchain}", "--version"],
                 ["cargo", f"+{toolchain}", "--version"],
                 ["cargo", f"+{toolchain}", "clippy", "--version"]):
        try:
            res = run(tool, timeout=60)
            ok = res.returncode == 0
            report(OK if ok else FAIL, " ".join(tool[:3]),
                   (res.stdout or res.stderr).strip().splitlines()[0] if (res.stdout or res.stderr) else "")
        except FileNotFoundError:
            report(FAIL, tool[0], "not installed (install rustup)")


def load_configs() -> tuple[dict, dict, list]:
    import tomllib
    cfg = tomllib.loads((MP4 / "configs/pipeline.toml").read_text())
    projects = tomllib.loads((MP4 / cfg["pipeline"]["projects_file"]).read_text())
    tools = json.loads((MP4 / cfg["pipeline"]["tools_file"]).read_text())
    report(OK, "configs parse", f"{len(projects)} projects, {len(tools)} agent tools")
    return cfg, projects, tools


def check_paths(cfg: dict, projects: dict) -> None:
    missing = [p for key in ("system_prompt", "translate_prompt", "repair_prompt")
               if not (MP4 / (p := cfg["agent"][key])).exists()]
    for pid, proj in projects.items():
        for src in proj["c_sources"]:
            if not (MP4 / proj["c_dir"] / src).exists():
                missing.append(f"{proj['c_dir']}/{src}")
        spec = MP4 / proj["rust_spec_dir"]
        for rel in ["Cargo.toml", *proj["test_files"],
                    *[f"src/interfaces/{m}.rs" for m in proj["modules"]]]:
            if not (spec / rel).exists():
                missing.append(f"{proj['rust_spec_dir']}/{rel}")
        for d in (proj["output_dir"], proj["trajectory_dir"]):
            if not (MP4 / d).is_dir():
                missing.append(d)
    report(FAIL if missing else OK, "config paths", ", ".join(missing) or "all present")


def check_specs_compile(cfg: dict, projects: dict) -> None:
    toolchain = cfg["pipeline"]["toolchain"]
    for pid, proj in projects.items():
        with tempfile.TemporaryDirectory() as tmp:
            crate = Path(tmp) / proj["crate_name"]
            shutil.copytree(MP4 / proj["rust_spec_dir"], crate,
                            ignore=shutil.ignore_patterns("target", ".git"))
            for m in proj["modules"]:
                shutil.copy(crate / "src/interfaces" / f"{m}.rs", crate / "src" / f"{m}.rs")
            res = run(["cargo", f"+{toolchain}", "check", "--all-targets"], cwd=crate)
            n_tests = sum((crate / t).read_text().count("#[test]") for t in proj["test_files"])
            detail = f"{proj['name']}: {n_tests} benchmark tests"
            if res.returncode != 0:
                errs = [l for l in res.stderr.splitlines() if l.startswith("error")]
                detail += f"; {len(errs)} error(s): " + "; ".join(errs[:3])
            report(OK if res.returncode == 0 else FAIL, f"spec skeleton compiles [{pid}]", detail)


def http_json(url: str, key: str, body: dict | None = None, timeout: int = 120) -> dict:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def check_provider(name: str, cfg: dict, all_models: bool = False) -> None:
    prov = cfg["providers"][name]
    base = prov["base_url"].rstrip("/")
    key = os.environ.get(prov["api_key_env"], "") if prov["api_key_env"] else ""
    if prov["api_key_env"] and not key:
        report(SKIP, f"provider {name}", f"{prov['api_key_env']} not set (configs/.env or shell)")
        return
    label = f"provider {name}"
    try:
        models = http_json(f"{base}/models", key, timeout=30)
        ids = {m.get("id", "").removeprefix("models/") for m in models.get("data", [])}
        wanted = [m["id"] for m in prov["models"]]
        missing = [m for m in wanted if m not in ids]
        report(FAIL if len(missing) == len(wanted) else OK, f"{label} /models",
               f"{len(ids)} models; {len(wanted) - len(missing)}/{len(wanted)} configured models listed"
               + (f"; not listed: {missing}" if missing else ""))
    except urllib.error.HTTPError as e:
        report(FAIL, f"{label} /models", f"HTTP {e.code}: {redact(e.read().decode()[:300], cfg)}")
        return
    except (urllib.error.URLError, TimeoutError) as e:
        report(FAIL, f"{label} /models", f"unreachable: {e}")
        return

    # Same policy as the pipeline: retry transient 5xx, move to the next model on
    # 429/quota or persistent 5xx. Passes if any configured model makes the tool call.
    # With all_models=True every model is probed once (costs 1 request each).
    waits = cfg["model"]["retry_on_5xx_seconds"]
    problems: list[str] = []
    working: list[str] = []
    for model in [m["id"] for m in prov["models"]]:
        for attempt in range(len(waits) + 1):
            result = tool_call_probe(model, base, key, cfg)
            if result["status"] == "retry" and attempt < len(waits):
                time.sleep(waits[attempt])
                continue
            break
        if result["status"] == "ok":
            working.append(model)
            if all_models:
                report(OK, f"{label} tool calling [{model}]", result["detail"])
            else:
                note = f"; skipped: {'; '.join(problems)}" if problems else ""
                report(OK, f"{label} tool calling", result["detail"] + note)
                return
        else:
            problems.append(f"{model}: {result['detail']}")
            if all_models:
                status = SKIP if result["status"] == "retry" else FAIL
                report(status, f"{label} tool calling [{model}]", result["detail"])
    if not working:
        report(FAIL, f"{label} tool calling", " | ".join(problems))


def tool_call_probe(model: str, base: str, key: str, cfg: dict) -> dict:
    """One small function-calling request. status: ok | retry (5xx) | fail."""
    inf = cfg["inference"]
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Use the add tool to compute 2 + 3."}],
        "tools": [{"type": "function", "function": {
            "name": "add", "description": "Add two integers.",
            "parameters": {"type": "object",
                           "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                           "required": ["a", "b"]}}}],
        "tool_choice": inf["tool_choice"],
        "temperature": inf["temperature"],
        "top_p": inf["top_p"],
        "max_tokens": 512,
    }
    try:
        resp = http_json(f"{base}/chat/completions", key, body, timeout=inf["request_timeout_seconds"])
        calls = resp["choices"][0]["message"].get("tool_calls") or []
        got = calls[0]["function"] if calls else None
        served = resp.get("model", model)
        if got and got["name"] == "add":
            return {"status": "ok", "detail": f"served by {served}: add({got['arguments']})"}
        return {"status": "fail", "detail": "no tool call returned"}
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode())
            msg = (msg[0] if isinstance(msg, list) else msg)["error"]["message"]
        except (ValueError, KeyError, IndexError, TypeError):
            msg = ""
        detail = f"HTTP {e.code} {redact(msg[:160], cfg)}".strip()
        return {"status": "retry" if e.code >= 500 else "fail", "detail": detail}
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
        return {"status": "retry", "detail": f"{type(e).__name__}: {e}"}


def check_ollama(cfg: dict, all_models: bool = False) -> None:
    prov = cfg["providers"]["ollama"]
    if not shutil.which("ollama"):
        report(SKIP, "provider ollama", "ollama not installed (optional)")
        return
    try:
        res = run(["ollama", "list"], timeout=20)
    except subprocess.TimeoutExpired:
        report(SKIP, "provider ollama", "ollama server not responding (optional)")
        return
    model = prov["models"][0]["id"]
    if model.split(":")[0] not in res.stdout:
        report(SKIP, "provider ollama", f"model {model} not pulled (optional: ollama pull {model})")
        return
    check_provider("ollama", cfg, all_models)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-network", action="store_true", help="skip model provider checks")
    ap.add_argument("--provider", choices=["gemini", "openrouter", "ollama"], help="check only this provider")
    ap.add_argument("--all-models", action="store_true",
                    help="probe tool calling on every configured model (1 request each)")
    args = ap.parse_args()

    load_env_file(MP4 / "configs/.env")
    check_python()
    cfg, projects, _tools = load_configs()
    check_toolchain(cfg["pipeline"]["toolchain"])
    check_paths(cfg, projects)
    check_specs_compile(cfg, projects)

    if args.no_network:
        report(SKIP, "providers", "--no-network")
    else:
        for name in [args.provider] if args.provider else ["gemini", "openrouter", "ollama"]:
            if name == "ollama":
                check_ollama(cfg, args.all_models)
            else:
                check_provider(name, cfg, args.all_models)

    print(f"\n{len(failures)} failing check(s)" + (f": {', '.join(failures)}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
