#!/usr/bin/env python3
"""Approximate unsafe-metrics scanner for a Rust crate.

Placeholder for the instructional team's unsafe-metrics tool (set
`[unsafe_metrics].command` in configs/pipeline.toml to use theirs). It scans the
crate's own sources (src/**/*.rs except src/bin/ tests and the unused
src/interfaces/ spec copy) after blanking comments and string literals.

Primary metrics (as defined in the MP4 handout):
  unsafe_lines        non-empty lines inside `unsafe { }` blocks / `unsafe fn` bodies
  unsafe_calls        call expressions inside unsafe regions (approximation)
  unsafe_casts        `as *const T` / `as *mut T`, transmute, pointer `.cast()`, from_raw_parts
  pointer_arithmetic  .add/.sub/.offset/.byte_add/... on raw pointers
Extra: unsafe_blocks, unsafe_fns, unsafe_impls, raw_pointer_types, ffi, manual_alloc,
forbid_unsafe_code (whether lib.rs has #![forbid(unsafe_code)]).

Usage: python3 src/unsafe_metrics.py <crate_dir>   -> JSON on stdout
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PRIMARY = ["unsafe_lines", "unsafe_calls", "unsafe_casts", "pointer_arithmetic"]
NOT_CALLS = {"if", "while", "for", "match", "return", "loop", "Some", "Ok", "Err", "fn", "in", "as"}


def blank_comments_and_strings(src: str) -> str:
    """Replace comments and string/char literals with spaces (newlines kept)."""
    out, i, n = [], 0, len(src)
    while i < n:
        c, nxt = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and nxt == "*":
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth += 1; j += 2
                elif src.startswith("*/", j):
                    depth -= 1; j += 2
                else:
                    j += 1
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c == '"' or (c == "r" and re.match(r'r#*"', src[i:i + 4]) and not src[i - 1:i].isalnum()):
            if c == "r":
                hashes = len(re.match(r'r(#*)"', src[i:]).group(1))
                end = src.find('"' + "#" * hashes, i + 2 + hashes)
                j = n if end == -1 else end + 1 + hashes
            else:
                j = i + 1
                while j < n and src[j] != '"':
                    j += 2 if src[j] == "\\" else 1
                j += 1
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c == "'" and re.match(r"'(\\.|[^\\'])'", src[i:i + 4] + src[i + 4:i + 12]):
            m = re.match(r"'(\\[^']*|[^\\'])'", src[i:])
            j = i + (len(m.group(0)) if m else 1)
            out.append(" " * (j - i)); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def match_brace(code: str, open_idx: int) -> int:
    depth = 0
    for j in range(open_idx, len(code)):
        if code[j] == "{":
            depth += 1
        elif code[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return len(code) - 1


def scan_file(path: Path, rel: str) -> dict:
    raw = path.read_text(errors="replace")
    code = blank_comments_and_strings(raw)
    m = dict.fromkeys(PRIMARY + ["unsafe_blocks", "unsafe_fns", "unsafe_impls", "raw_pointer_types",
                                 "ffi", "manual_alloc", "transmute"], 0)
    locations = []
    regions = []
    for kw in re.finditer(r"\bunsafe\b", code):
        rest = code[kw.end():]
        stripped = rest.lstrip()
        if stripped.startswith("{"):
            m["unsafe_blocks"] += 1
            start = kw.end() + rest.index("{")
            regions.append((start, match_brace(code, start)))
        elif re.match(r"(extern\s+\"?\w*\"?\s*)?fn\b", stripped):
            m["unsafe_fns"] += 1
            brace, semi = code.find("{", kw.end()), code.find(";", kw.end())
            if brace != -1 and (semi == -1 or brace < semi):
                regions.append((brace, match_brace(code, brace)))
        elif stripped.startswith("impl"):
            m["unsafe_impls"] += 1
        line = code.count("\n", 0, kw.start()) + 1
        locations.append(f"{rel}:{line}: unsafe")
    unsafe_lines: set[int] = set()
    for start, end in regions:
        first = code.count("\n", 0, start) + 1
        seg_lines = code[start:end + 1].split("\n")
        for k, text in enumerate(seg_lines):
            if text.strip() and text.strip() not in ("{", "}"):
                unsafe_lines.add(first + k)
        for call in re.finditer(r"(?<![\w!])([A-Za-z_]\w*)\s*(::<[^>]*>)?\s*\(", code[start:end + 1]):
            if call.group(1) not in NOT_CALLS:
                m["unsafe_calls"] += 1
    m["unsafe_lines"] = len(unsafe_lines)

    def count(pattern, key):
        for hit in re.finditer(pattern, code):
            m[key] += 1
            locations.append(f"{rel}:{code.count(chr(10), 0, hit.start()) + 1}: {key} `{hit.group(0).strip()}`")

    count(r"\bas\s+\*\s*(const|mut)\b", "unsafe_casts")
    count(r"\btransmute(_copy)?\b", "unsafe_casts")
    count(r"\bfrom_raw_parts(_mut)?\b|\bBox::from_raw\b|\.cast::<|\.cast\(\)|\.cast_mut\(\)|\.cast_const\(\)",
          "unsafe_casts")
    count(r"\btransmute\b", "transmute")
    count(r"\.(byte_)?(wrapping_)?(add|sub|offset)\s*\(|\.offset_from\s*\(", "pointer_arithmetic")
    count(r"\*\s*(const|mut)\s+[A-Za-z_(\[]", "raw_pointer_types")
    count(r"\bextern\s+\"C\"|#\s*\[\s*link\b|\blibc::", "ffi")
    count(r"\b(alloc|dealloc|realloc|alloc_zeroed)\s*\(|\bLayout::|\bmalloc\b|\bfree\s*\(|mem::forget", "manual_alloc")
    # .add/.sub on numbers are fine: only count pointer arithmetic when raw pointers exist.
    if m["raw_pointer_types"] == 0 and m["unsafe_blocks"] == 0 and m["unsafe_fns"] == 0:
        locations = [l for l in locations if "pointer_arithmetic" not in l]
        m["pointer_arithmetic"] = 0
    return {"metrics": m, "locations": locations}


def scan_crate(crate: Path) -> dict:
    totals: dict[str, int] = {}
    locations: list[str] = []
    files = []
    for f in sorted((crate / "src").rglob("*.rs")):
        rel = f.relative_to(crate).as_posix()
        if rel.startswith(("src/bin/", "src/interfaces/")):
            continue
        files.append(rel)
        res = scan_file(f, rel)
        for k, v in res["metrics"].items():
            totals[k] = totals.get(k, 0) + v
        locations += res["locations"]
    lib = crate / "src/lib.rs"
    lib_code = blank_comments_and_strings(lib.read_text()) if lib.exists() else ""
    totals["forbid_unsafe_code"] = int(bool(re.search(r"#!\s*\[\s*forbid\s*\(\s*unsafe_code", lib_code)))
    totals["primary_total"] = sum(totals.get(k, 0) for k in PRIMARY)
    return {"tool": "builtin-approximate", "files": files, "metrics": totals, "locations": locations[:200]}


def run_metrics(crate: Path, command: str = "") -> dict:
    """Use the instructional team's tool if configured, otherwise the built-in scanner."""
    if not command:
        return scan_crate(crate)
    cmd = [part.replace("{crate}", str(crate)) for part in shlex.split(command)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = {"tool": command, "raw_output": res.stdout[-20000:] + res.stderr[-4000:], "returncode": res.returncode}
    try:
        parsed = json.loads(res.stdout)
        flat = parsed.get("metrics", parsed) if isinstance(parsed, dict) else {}
        out["metrics"] = {k: v for k, v in flat.items() if isinstance(v, (int, float))}
    except ValueError:
        out["metrics"] = {}
    builtin = scan_crate(crate)          # always keep our numbers for comparison
    for k in PRIMARY:
        out["metrics"].setdefault(k, builtin["metrics"][k])
    out["metrics"]["primary_total"] = sum(out["metrics"][k] for k in PRIMARY)
    out["metrics"].setdefault("forbid_unsafe_code", builtin["metrics"]["forbid_unsafe_code"])
    out["builtin"] = builtin["metrics"]
    out["locations"] = builtin["locations"]
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(scan_crate(Path(sys.argv[1])), indent=2))
