#!/usr/bin/env python3
"""Unsafe metrics via the instructional team's NewMetrics tool (the only safety tool used).

Runs `[unsafe_metrics].command` (src/newmetrics/run_newmetrics.sh: `cargo newmetrics |
aggregate.py`) on a crate and returns the aggregated metrics plus the source locations
NewMetrics records (unsafe_spans.txt, decls.txt, derefs.txt), which are shown to the agent.

Primary metrics: unsafe_lines, unsafe_calls, unsafe_casts, pointer_arithmetic.
Extra metrics from the tool: raw_pointer_dereferences, raw_pointer_declarations,
total_spans, unsafe_ratio.  `forbid_unsafe_code` records whether src/lib.rs carries
#![forbid(unsafe_code)] (used only to remind the agent to add it).

Usage: python3 src/unsafe_metrics.py <crate_dir>   -> JSON on stdout
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

PRIMARY = ["unsafe_lines", "unsafe_calls", "unsafe_casts", "pointer_arithmetic"]
MP4 = Path(__file__).resolve().parent.parent
SPAN_FILES = {"unsafe_spans.txt": "unsafe span", "decls.txt": "raw-pointer declaration",
              "derefs.txt": "raw-pointer dereference"}


class UnsafeMetricsError(RuntimeError):
    """NewMetrics is missing or failed; the pipeline does not fall back to anything else."""


def _forbid_present(crate: Path) -> int:
    lib = crate / "src/lib.rs"
    return int(lib.exists() and bool(re.search(r"#!\s*\[\s*forbid\s*\(\s*unsafe_code", lib.read_text())))


def _locations(art: Path) -> list[str]:
    """NewMetrics span files: alternating `file:l:c: l:c` header lines and source snippets."""
    out = []
    for name, label in SPAN_FILES.items():
        f = art / name
        if not f.exists():
            continue
        cur = None
        for line in f.read_text(errors="replace").splitlines():
            if re.match(r"^\S+\.rs:\d+:\d+: \d+:\d+$", line):
                cur = line
                out.append(f"{label} at {line}")
            elif cur and line.strip() and len(out[-1]) < 300:
                out[-1] += " | " + line.strip()
    return out


def run_metrics(crate: Path, command: str = "") -> dict:
    if not command:
        command = tomllib.loads((MP4 / "configs/pipeline.toml").read_text())["unsafe_metrics"]["command"]
    with tempfile.TemporaryDirectory() as art:
        cmd = [p.replace("{crate}", str(crate)).replace("{mp4}", str(MP4)) for p in shlex.split(command)]
        cmd.append("/dev/null")       # summary.json destination (the JSON is read from stdout)
        cmd.append(art)               # where NewMetrics' span files are moved
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise UnsafeMetricsError(f"NewMetrics could not run: {e}") from e
        if res.returncode != 0:
            raise UnsafeMetricsError(f"NewMetrics failed (exit {res.returncode}): {res.stderr.strip()[-500:]}")
        try:
            metrics = {k: v for k, v in json.loads(res.stdout).items() if isinstance(v, (int, float))}
        except ValueError as e:
            raise UnsafeMetricsError(f"NewMetrics output was not JSON: {res.stdout[-300:]}") from e
        missing = [k for k in PRIMARY if k not in metrics]
        if missing:
            raise UnsafeMetricsError(f"NewMetrics output lacks {missing}")
        locations = _locations(Path(art))
    metrics["primary_total"] = sum(metrics[k] for k in PRIMARY)
    metrics["forbid_unsafe_code"] = _forbid_present(crate)
    return {"tool": "NewMetrics (cargo newmetrics | aggregate.py)", "metrics": metrics, "locations": locations[:60]}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(run_metrics(Path(sys.argv[1]).resolve()), indent=2))
