"""Trajectory logging. Everything passes through the Redactor before hitting disk."""
from __future__ import annotations

import json
from pathlib import Path

from common import Redactor, now_iso


class Trajectory:
    def __init__(self, root: Path, redactor: Redactor):
        self.root = root
        self.redact = redactor
        self.iteration = 0
        root.mkdir(parents=True, exist_ok=True)
        self.events_path = root / "events.jsonl"

    def event(self, kind: str, **data) -> None:
        rec = {"ts": now_iso(), "iteration": self.iteration, "event": kind, **data}
        line = self.redact(json.dumps(self.redact.obj(rec), ensure_ascii=False))
        with self.events_path.open("a") as f:
            f.write(line + "\n")

    def write_json(self, rel: str, obj) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.redact(json.dumps(self.redact.obj(obj), indent=2, ensure_ascii=False)))
        return path

    def write_text(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.redact(text))
        return path
