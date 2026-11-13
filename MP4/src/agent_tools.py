"""Tool implementations exposed to the agent (schemas in configs/tools.json).

The agent sees two roots: `c/` (the original C project, read-only) and `rust/`
(the crate being translated). Writes are confined to rust/src/ minus protected
paths (benchmark tests and the interface spec copy).
"""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

from common import truncate
from evaluate import Evaluator

TEXT_SUFFIXES = {".c", ".h", ".rs", ".toml", ".md", ".txt", "", ".lock", ".cfg", ".mk"}
SKIP_DIRS = {"target", ".git"}


class ToolError(Exception):
    pass


class Workspace:
    def __init__(self, c_root: Path, rust_root: Path, protected_globs: list[str]):
        self.roots = {"c": c_root.resolve(), "rust": rust_root.resolve()}
        self.protected = protected_globs

    def resolve(self, path: str) -> tuple[str, Path, str]:
        path = (path or "").strip().lstrip("./") or "."
        if path in (".", ""):
            raise ToolError("path must start with 'c/' or 'rust/'")
        root_name, _, rest = path.partition("/")
        if root_name not in self.roots:
            raise ToolError(f"unknown root in '{path}': paths must start with 'c/' or 'rust/'")
        root = self.roots[root_name]
        full = (root / rest).resolve()
        if full != root and root not in full.parents:
            raise ToolError("path escapes the workspace")
        return root_name, full, full.relative_to(root).as_posix() if full != root else ""

    def check_writable(self, path: str) -> Path:
        root_name, full, rel = self.resolve(path)
        if root_name != "rust" or not rel.startswith("src/") or not rel.endswith(".rs"):
            raise ToolError("you may only write .rs files under rust/src/")
        if any(fnmatch.fnmatch(rel, g) for g in self.protected):
            raise ToolError(f"{path} is protected (benchmark tests / interface spec) and cannot be modified")
        return full

    def display(self, full: Path) -> str:
        for name, root in self.roots.items():
            if full == root or root in full.parents:
                return f"{name}/{full.relative_to(root).as_posix()}" if full != root else f"{name}/"
        return str(full)


class ToolExecutor:
    def __init__(self, ws: Workspace, evaluator: Evaluator, cfg: dict):
        self.ws, self.ev, self.cfg = ws, evaluator, cfg
        self.limit = cfg["agent"]["tool_output_char_limit"]
        self.files_read: set[str] = set()
        self.files_written: set[str] = set()

    def execute(self, name: str, args: dict) -> tuple[str, dict]:
        """Return (text for the model, structured info for the trajectory)."""
        handler = getattr(self, f"tool_{name}", None)
        if handler is None:
            return f"ERROR: unknown tool '{name}'", {"ok": False}
        try:
            text, info = handler(**args)
            return truncate(text, self.limit), {"ok": True, **info}
        except ToolError as e:
            return f"ERROR: {e}", {"ok": False, "error": str(e)}
        except TypeError as e:
            return f"ERROR: bad arguments for {name}: {e}", {"ok": False, "error": str(e)}

    # ------------------------------------------------------------ file tools
    def tool_list_files(self, path: str = "rust/"):
        _, full, _ = self.ws.resolve(path)
        if not full.is_dir():
            raise ToolError(f"{path} is not a directory")
        out = []
        for f in sorted(full.rglob("*")):
            if any(part in SKIP_DIRS for part in f.relative_to(full).parts) or not f.is_file():
                continue
            lines = f.read_text(errors="replace").count("\n") if f.suffix in TEXT_SUFFIXES else None
            out.append(f"{self.ws.display(f)}" + (f"  ({lines} lines)" if lines is not None else "  (binary)"))
        return "\n".join(out) or "(empty)", {}

    def tool_read_file(self, path: str, start_line: int | None = None, end_line: int | None = None):
        _, full, _ = self.ws.resolve(path)
        if not full.is_file():
            raise ToolError(f"{path} does not exist")
        if full.suffix not in TEXT_SUFFIXES:
            raise ToolError(f"{path} is not a text source file")
        lines = full.read_text(errors="replace").splitlines()
        s = max(1, start_line or 1)
        e = min(len(lines), end_line or len(lines))
        self.files_read.add(self.ws.display(full))
        body = "\n".join(f"{i:5d}| {lines[i - 1]}" for i in range(s, e + 1))
        return f"{self.ws.display(full)} lines {s}-{e} of {len(lines)}\n{body}", {"file": self.ws.display(full)}

    def tool_search(self, pattern: str, path: str | None = None):
        try:
            rx = re.compile(pattern)
        except re.error as e:
            raise ToolError(f"invalid regex: {e}")
        roots = [self.ws.resolve(path)[1]] if path else list(self.ws.roots.values())
        hits = []
        for root in roots:
            files = [root] if root.is_file() else sorted(root.rglob("*"))
            for f in files:
                if not f.is_file() or f.suffix not in TEXT_SUFFIXES or any(p in SKIP_DIRS for p in f.parts):
                    continue
                for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                    if rx.search(line):
                        hits.append(f"{self.ws.display(f)}:{n}: {line.strip()[:200]}")
        return "\n".join(hits[:200]) + (f"\n... {len(hits) - 200} more" if len(hits) > 200 else "") or "no matches", {}

    def tool_write_file(self, path: str, content: str):
        full = self.ws.check_writable(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content if content.endswith("\n") else content + "\n")
        self.files_written.add(self.ws.display(full))
        return f"wrote {self.ws.display(full)} ({content.count(chr(10)) + 1} lines)", {"file": self.ws.display(full),
                                                                                     "chars": len(content)}

    def tool_replace_in_file(self, path: str, old_text: str, new_text: str):
        full = self.ws.check_writable(path)
        if not full.exists():
            raise ToolError(f"{path} does not exist")
        text = full.read_text()
        n = text.count(old_text)
        if n != 1:
            raise ToolError(f"old_text found {n} times in {path}; it must match exactly once "
                            "(include more surrounding lines, or read_file to see the current text)")
        full.write_text(text.replace(old_text, new_text))
        self.files_written.add(self.ws.display(full))
        return f"replaced 1 occurrence in {self.ws.display(full)}", {"file": self.ws.display(full)}

    # ------------------------------------------------------------ feedback tools
    def tool_cargo(self, command: str):
        if command in ("check", "build"):
            b = self.ev.build(command)
            if b["ok"]:
                own = [w for w in b["warnings"] if not (w["file"] or "").startswith("src/bin/")]
                text = f"cargo {command}: OK, {len(own)} warning(s) in src"
                if own:
                    text += "\n" + "\n".join(w["rendered"] for w in own[:10])
            else:
                text = f"cargo {command}: FAILED with {len(b['errors'])} error(s)\n" + \
                       "\n".join(e["rendered"] for e in b["errors"][:20])
            return text, {"ok_build": b["ok"], "errors": len(b["errors"]), "warnings": len(b["warnings"])}
        if command == "test":
            t = self.ev.tests()
            if not t["compiled"]:
                return "cargo test: test build FAILED\n" + "\n".join(t["compile_errors"]), {"passed": 0}
            lines = [f"cargo test: {t['passed']}/{t['total']} benchmark tests passed"]
            lines += [f"  {k}: {v}" for k, v in t["status"].items()]
            for f in t["failures"]:
                lines.append(f"\n---- {f['test']} ----\n{f['message']}")
            return "\n".join(lines), {"passed": t["passed"], "total": t["total"]}
        if command == "clippy":
            c = self.ev.clippy()
            if not c["compiled"]:
                return "cargo clippy: crate does not compile; run `cargo check` first", {}
            head = "cargo clippy: " + ", ".join(f"{k}={v['src']}" for k, v in c["categories"].items()) + \
                   f" (total {c['src_total']} in src; {c['tests_total']} in read-only tests ignored)"
            body = "\n".join(f"[{w['category']}] {w['rendered']}" for w in c["warnings"][:30])
            return head + ("\n" + body if body else ""), {"categories": c["categories"]}
        raise ToolError("command must be one of check, build, test, clippy")

    def tool_unsafe_metrics(self):
        u = self.ev.unsafe()
        text = json.dumps(u["metrics"]) + ("\n" + "\n".join(u.get("locations", [])[:40]) if u.get("locations") else "")
        return text, {"metrics": u["metrics"]}

    def tool_finish(self, summary: str = ""):
        return "Iteration finished. The controller will now evaluate the crate.", {"finished": True,
                                                                                    "summary": summary}
