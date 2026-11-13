"""Shared helpers: config loading, secrets handling, subprocess, text utilities."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import tomllib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MP4 = Path(__file__).resolve().parent.parent


def load_env_file(path: Path = MP4 / "configs/.env") -> None:
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


def load_config() -> dict:
    """Return the pipeline config with `projects` and `tools` merged in."""
    cfg = tomllib.loads((MP4 / "configs/pipeline.toml").read_text())
    cfg["projects"] = tomllib.loads((MP4 / cfg["pipeline"]["projects_file"]).read_text())
    cfg["tools"] = json.loads((MP4 / cfg["pipeline"]["tools_file"]).read_text())
    return cfg


class Redactor:
    """Scrubs API keys and key-shaped strings from anything written to disk."""

    def __init__(self, cfg: dict):
        self.values = [os.environ[e] for e in cfg["trajectory"]["redact_env"] if os.environ.get(e)]
        self.patterns = [re.compile(p) for p in cfg["trajectory"]["redact_patterns"]]

    def __call__(self, text: str) -> str:
        for v in self.values:
            text = text.replace(v, "<REDACTED>")
        for p in self.patterns:
            text = p.sub("<REDACTED>", text)
        return text

    def obj(self, obj):
        if isinstance(obj, str):
            return self(obj)
        if isinstance(obj, dict):
            return {k: self.obj(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self.obj(v) for v in obj]
        return obj


def run_cmd(cmd: list[str], cwd: Path, timeout: int) -> dict:
    """Run a command; never raises on failure or timeout."""
    start = time.time()
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": " ".join(cmd), "returncode": res.returncode, "stdout": res.stdout,
                "stderr": res.stderr, "timed_out": False, "seconds": round(time.time() - start, 1)}
    except subprocess.TimeoutExpired as e:
        def dec(b):
            return b.decode(errors="replace") if isinstance(b, bytes) else (b or "")
        return {"cmd": " ".join(cmd), "returncode": -1, "stdout": dec(e.stdout), "stderr": dec(e.stderr),
                "timed_out": True, "seconds": round(time.time() - start, 1)}


def truncate(text: str, limit: int) -> str:
    """Keep the head and tail of long text."""
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    tail = limit - head
    return f"{text[:head]}\n... [{len(text) - limit} chars truncated] ...\n{text[-tail:]}"


def fill_template(template: str, values: dict) -> str:
    """Replace {name} placeholders (only known keys, so code braces are safe)."""
    for k, v in values.items():
        template = template.replace("{" + k + "}", str(v))
    return template


def pacific_date() -> str:
    """Gemini free-tier daily quotas reset at midnight Pacific time."""
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def estimate_tokens(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False)) // 4
