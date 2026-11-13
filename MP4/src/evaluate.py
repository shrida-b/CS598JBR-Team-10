"""Independent evaluation of a translated crate: integrity, build, tests,
Clippy (per category), unsafe metrics, and a comparable score."""
from __future__ import annotations

import fnmatch
import json
import re
import shutil
from pathlib import Path

from common import run_cmd, truncate
from unsafe_metrics import blank_comments_and_strings, run_metrics


def strip_lifetimes(sig: str) -> str:
    """Lifetime annotations that elision would infer do not change a signature for callers."""
    sig = re.sub(r"&\s*'\w+\s+", "&", sig)                 # &'a T  -> &T
    sig = re.sub(r"'\w+\s*:\s*'\w+\s*", "", sig)          # 'a: 'b bounds
    sig = re.sub(r"<\s*(?:'\w+\s*,?\s*)+>", "", sig)       # <'a> / <'a, 'b>
    sig = re.sub(r"(<)\s*'\w+\s*,\s*", r"\1", sig)         # <'a, T> -> <T>
    sig = re.sub(r"\s*,\s*'\w+\s*(?=[,>])", "", sig)       # <T, 'a> -> <T>
    return sig


class Evaluator:
    def __init__(self, cfg: dict, project: dict, crate: Path, spec: Path):
        self.cfg, self.project, self.crate, self.spec = cfg, project, crate, spec
        self.ev = cfg["evaluation"]
        self.timeout = self.ev["command_timeout_seconds"]
        self.test_names = []
        for t in project["test_files"]:
            self.test_names += re.findall(r"#\[test\]\s*(?:#\[[^\]]*\]\s*)*fn\s+(\w+)", (spec / t).read_text())

    # ----------------------------------------------------------- cargo helpers
    def _cargo_json(self, cmd: list[str]) -> dict:
        res = run_cmd(cmd, self.crate, self.timeout)
        msgs = []
        for line in res["stdout"].splitlines():
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get("reason") == "compiler-message":
                msg = m["message"]
                span = next((s for s in msg.get("spans", []) if s.get("is_primary")), None)
                msgs.append({
                    "level": msg.get("level"),
                    "code": (msg.get("code") or {}).get("code"),
                    "file": span["file_name"] if span else None,
                    "line": span["line_start"] if span else None,
                    "message": msg.get("message"),
                    "rendered": msg.get("rendered") or msg.get("message"),
                    "target": m.get("target", {}).get("src_path", ""),
                })
        res["messages"] = msgs
        return res

    def build(self, sub: str = "build") -> dict:
        base = self.ev["build"] if sub == "build" else self.ev["check"]
        res = self._cargo_json(base + ["--message-format=json"])
        errors = [m for m in res["messages"] if m["level"] == "error"]
        warnings = [m for m in res["messages"] if m["level"] == "warning"]
        ok = res["returncode"] == 0
        if not ok and not errors:      # e.g. manifest problems: no JSON messages
            errors = [{"rendered": truncate(res["stderr"], 4000), "file": None, "line": None, "code": None,
                       "message": "cargo failed"}]
        return {"ok": ok, "errors": errors, "warnings": warnings, "timed_out": res["timed_out"]}

    def tests(self) -> dict:
        res = run_cmd(self.ev["test"], self.crate, self.ev.get("test_timeout_seconds", self.timeout))
        out = res["stdout"] + "\n" + res["stderr"]
        status = {}
        for name, verdict in re.findall(r"^test (\S+) \.\.\. (ok|FAILED|ignored)", out, re.M):
            short = name.split("::")[-1]
            if short in self.test_names:
                status[short] = verdict
        failures = []
        for block in re.split(r"^---- ", out, flags=re.M)[1:]:
            header, _, body = block.partition("\n")
            name = header.split(" ")[0].split("::")[-1]
            if name in self.test_names:
                body = body.split("\nfailures:")[0].split("\n---- ")[0]
                failures.append({"test": name, "message": truncate(body.strip(), 1500)})
        compiled = bool(status) or "test result:" in out
        compile_errors = [] if compiled else [truncate(res["stderr"], 6000)]
        for name in self.test_names:
            if name not in status:
                status[name] = "TIMEOUT" if res["timed_out"] else "NOT RUN"
        passed = sum(1 for v in status.values() if v == "ok")
        return {"compiled": compiled, "passed": passed, "total": len(self.test_names), "status": status,
                "failures": failures, "compile_errors": compile_errors, "timed_out": res["timed_out"]}

    def clippy(self) -> dict:
        """Count clippy warnings per category (one run per category) plus the graders' exact command."""
        cats = self.ev["clippy_categories"]
        base = self.ev["clippy"][: self.ev["clippy"].index("--")]
        per_cat, warnings = {}, []
        compiled = True
        for cat in cats:
            res = self._cargo_json(base + ["--", "-A", "clippy::all", "-W", f"clippy::{cat}"])
            if res["returncode"] != 0 and any(m["level"] == "error" and not (m["code"] or "").startswith("clippy")
                                              for m in res["messages"]):
                compiled = False
            src = tests = 0
            for m in res["messages"]:
                if not (m["code"] or "").startswith("clippy::"):
                    continue
                in_tests = (m["file"] or "").startswith("src/bin/")
                tests += in_tests
                src += not in_tests
                if not in_tests:
                    warnings.append({"category": cat, "lint": m["code"], "file": m["file"], "line": m["line"],
                                     "message": m["message"], "rendered": m["rendered"]})
            per_cat[cat] = {"src": src, "tests": tests}
        grader = self._cargo_json(self.ev["clippy"])
        g_clippy = [m for m in grader["messages"] if (m["code"] or "").startswith("clippy::")]
        return {
            "compiled": compiled,
            "categories": per_cat,
            "src_total": sum(v["src"] for v in per_cat.values()),
            "tests_total": sum(v["tests"] for v in per_cat.values()),
            "grader_command": {"clippy_warnings": len(g_clippy),
                               "clippy_warnings_src": sum(1 for m in g_clippy if not (m["file"] or "").startswith("src/bin/")),
                               "rustc_warnings": sum(1 for m in grader["messages"]
                                                     if m["level"] == "warning" and not (m["code"] or "").startswith("clippy::"))},
            "warnings": warnings,
        }

    def unsafe(self) -> dict:
        return run_metrics(self.crate, self.cfg["unsafe_metrics"]["command"])

    # ----------------------------------------------------------- integrity
    def integrity(self, restore: bool = True) -> dict:
        violations, restored = [], []
        globs = self.cfg["integrity"]["protected_globs"]
        for f in self.spec.rglob("*"):
            rel = f.relative_to(self.spec).as_posix()
            if f.is_file() and any(fnmatch.fnmatch(rel, g) for g in globs) and ".git/" not in rel:
                dst = self.crate / rel
                if not dst.exists() or dst.read_bytes() != f.read_bytes():
                    violations.append(f"protected file modified or missing: {rel}")
                    if restore:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dst)
                        restored.append(rel)
        bin_dir = self.crate / "src/bin"
        for f in bin_dir.rglob("*") if bin_dir.exists() else []:
            if f.is_file() and not (self.spec / f.relative_to(self.crate)).exists():
                violations.append(f"unexpected file in protected dir: {f.relative_to(self.crate)}")
        lib = (self.crate / "src/lib.rs").read_text() if (self.crate / "src/lib.rs").exists() else ""
        for mod in self.project["modules"]:
            if not re.search(rf"\bpub\s+mod\s+{mod}\s*;", lib):
                violations.append(f"src/lib.rs no longer declares `pub mod {mod};`")
        src_text = self._own_sources_text()
        violations += self._signature_violations(src_text)
        for pat in self.cfg["integrity"]["forbid_patterns"]:
            if re.search(pat, src_text):
                violations.append(f"forbidden FFI pattern `{pat}` found in sources")
        violations += self._test_literal_leaks()
        return {"ok": not violations, "violations": violations, "restored": restored}

    def required_api(self) -> str:
        """Checklist of public items from the interface spec (auto-extracted, project-agnostic)."""
        lines = []
        for mod in self.project["modules"]:
            iface = blank_comments_and_strings((self.spec / "src/interfaces" / f"{mod}.rs").read_text())
            for kind, name in re.findall(r"\bpub\s+(struct|enum|type|trait)\s+(\w+)", iface):
                lines.append(f"- [{mod}] pub {kind} {name}")
            for m in re.finditer(r"\bpub\s+fn\s+\w+[^{;]*", iface):
                lines.append(f"- [{mod}] " + " ".join(m.group(0).split()))
        return "\n".join(lines)

    def interface_violations(self) -> list[str]:
        """Cheap subset of integrity() for the agent's own cargo check/build calls."""
        src_text = self._own_sources_text()
        out = self._signature_violations(src_text)
        lib = (self.crate / "src/lib.rs").read_text() if (self.crate / "src/lib.rs").exists() else ""
        out += [f"src/lib.rs no longer declares `pub mod {m};`" for m in self.project["modules"]
                if not re.search(rf"\bpub\s+mod\s+{m}\s*;", lib)]
        return out

    def _own_files(self) -> list[Path]:
        return [f for f in sorted((self.crate / "src").rglob("*.rs"))
                if not f.relative_to(self.crate).as_posix().startswith(("src/bin/", "src/interfaces/"))]

    def _own_sources_text(self) -> str:
        return "\n".join(blank_comments_and_strings(f.read_text()) for f in self._own_files())

    @staticmethod
    def _signatures(code: str) -> dict:
        """name -> set of normalized `pub fn` signatures (parameter names dropped)."""
        sigs: dict[str, set] = {}
        for m in re.finditer(r"\bpub\s+fn\s+(\w+)", code):
            i, depth = m.end(), 0
            while i < len(code):
                ch = code[i]
                if ch in "(<[":
                    depth += 1
                elif ch in ")>]" and not (ch == ">" and code[i - 1] == "-"):
                    depth -= 1
                elif ch in "{;" and depth <= 0:
                    break
                i += 1
            sig = code[m.start():i]
            open_idx = sig.find("(")
            if open_idx == -1:
                continue
            d, close_idx = 0, len(sig)
            for k in range(open_idx, len(sig)):
                d += sig[k] == "("
                d -= sig[k] == ")"
                if d == 0:
                    close_idx = k
                    break
            head, params, ret = sig[:open_idx], sig[open_idx + 1:close_idx], sig[close_idx + 1:]
            parts, buf, d = [], "", 0
            for ch in params:
                if ch == "," and d == 0:
                    parts.append(buf); buf = ""
                    continue
                d += ch in "(<["
                d -= ch in ")>]"
                buf += ch
            parts.append(buf)
            types = []
            for p in parts:
                # `mut x: T` / `mut self` only change the binding, not the signature
                p = re.sub(r"^mut\s+", "", p.strip())
                if not p:
                    continue
                if re.fullmatch(r"&\s*('\w+\s+)?(mut\s+)?self", p) or p == "self":
                    types.append(p)
                else:
                    types.append(p.split(":", 1)[1] if ":" in p else p)
            norm = re.sub(r"\s+", "", strip_lifetimes(head + "(" + ",".join(types) + ")" + ret))
            sigs.setdefault(m.group(1), set()).add(norm)
        return sigs

    def _signature_violations(self, src_text: str) -> list[str]:
        out = []
        have = self._signatures(src_text)
        for mod in self.project["modules"]:
            iface = blank_comments_and_strings((self.spec / "src/interfaces" / f"{mod}.rs").read_text())
            for name, sigs in self._signatures(iface).items():
                for s in sigs:
                    if s not in have.get(name, set()):
                        out.append(f"public signature changed or missing: `{s}`")
            for kind, name in re.findall(r"\bpub\s+(struct|enum|type|trait)\s+(\w+)", iface):
                if not re.search(rf"\bpub\s+{kind}\s+{name}\b", src_text):
                    out.append(f"public {kind} `{name}` missing")
        return out

    def _test_literal_leaks(self) -> list[str]:
        """Flag long string literals copied from the tests into the implementation
        (a sign of special-casing benchmark inputs)."""
        own = "\n".join(f.read_text() for f in self._own_files())
        leaks = []
        for t in self.project["test_files"]:
            for lit in set(re.findall(r'"((?:[^"\\]|\\.){12,})"', (self.spec / t).read_text())):
                if "{" in lit or "failed" in lit.lower():      # assertion messages, not inputs
                    continue
                if lit in own:
                    leaks.append(f"test input literal copied into implementation: \"{lit[:60]}\"")
        return leaks

    # ----------------------------------------------------------- full report
    def full(self) -> dict:
        integrity = self.integrity()
        build = self.build("build")
        tests = self.tests() if build["ok"] else {
            "compiled": False, "passed": 0, "total": len(self.test_names),
            "status": dict.fromkeys(self.test_names, "NOT RUN"), "failures": [], "compile_errors": [],
            "timed_out": False}
        clippy = self.clippy() if build["ok"] else None
        unsafe = self.unsafe()
        report = {"integrity": integrity, "build": build, "tests": tests, "clippy": clippy, "unsafe": unsafe}
        report["score"] = score(report)
        report["success"] = is_success(report, self.cfg["stopping"]["clippy_target_total"])
        return report


def score(r: dict) -> list:
    """Lexicographic: builds → tests passed → fewer integrity violations → fewer unsafe → fewer clippy.
    Integrity violations lower the score (and block success) without discarding a translation
    that otherwise works; tampered protected files are restored before testing anyway."""
    clippy_total = r["clippy"]["src_total"] if r["clippy"] else 10**6
    return [int(r["build"]["ok"]), r["tests"]["passed"], -len(r["integrity"]["violations"]),
            -r["unsafe"]["metrics"]["primary_total"], -clippy_total]


def is_success(r: dict, clippy_target: int) -> bool:
    return (r["integrity"]["ok"] and r["build"]["ok"] and r["tests"]["passed"] == r["tests"]["total"]
            and r["unsafe"]["metrics"]["primary_total"] == 0
            and r["clippy"] is not None and r["clippy"]["src_total"] <= clippy_target)


# ------------------------------------------------------------- formatting
def status_table(r: dict) -> str:
    t, c, u = r["tests"], r["clippy"], r["unsafe"]["metrics"]
    cats = " / ".join(f"{k} {v['src']}" for k, v in c["categories"].items()) if c else "n/a (does not build)"
    rows = [
        ("Integrity", "OK" if r["integrity"]["ok"] else f"{len(r['integrity']['violations'])} violation(s)"),
        ("Build", "OK" if r["build"]["ok"] else f"FAILED ({len(r['build']['errors'])} error(s))"),
        ("Tests", f"{t['passed']}/{t['total']} passed"),
        ("Clippy (src)", f"{c['src_total'] if c else 'n/a'} [{cats}]"),
        ("Unsafe (primary total)", f"{u['primary_total']} [lines {u['unsafe_lines']}, calls {u['unsafe_calls']}, "
                                   f"casts {u['unsafe_casts']}, ptr-arith {u['pointer_arithmetic']}]"),
        ("#![forbid(unsafe_code)]", "present" if u.get("forbid_unsafe_code") else "missing"),
    ]
    return "| Check | Result |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows)


def feedback_sections(r: dict, limit: int) -> dict:
    integ = r["integrity"]
    integrity = "OK" if integ["ok"] else "\n".join(f"- {v}" for v in integ["violations"])
    if integ["restored"]:
        integrity += "\n(The controller restored these protected files: " + ", ".join(integ["restored"]) + ")"
    b = r["build"]
    build = "OK" if b["ok"] else truncate("\n".join(e["rendered"] for e in b["errors"][:15]), limit)
    if b["ok"] and b["warnings"]:
        build += f" ({len(b['warnings'])} rustc warnings, e.g.:)\n" + truncate(
            "\n".join(w["rendered"] for w in b["warnings"][:5]), limit // 4)
    t = r["tests"]
    if not b["ok"]:
        tests = "not run (build failed)"
    elif not t["compiled"]:
        tests = "test target failed to compile:\n" + truncate("\n".join(t["compile_errors"]), limit)
    else:
        lines = [f"{t['passed']}/{t['total']} passed."] + [f"- {k}: {v}" for k, v in t["status"].items() if v != "ok"]
        lines += [f"\n#### {f['test']}\n```\n{f['message']}\n```" for f in t["failures"]]
        tests = truncate("\n".join(lines), limit)
    c = r["clippy"]
    if not c:
        clippy = "not run (build failed)"
    else:
        clippy = (", ".join(f"{k}: {v['src']}" for k, v in c["categories"].items())
                  + f" (warnings inside the read-only tests are ignored: {c['tests_total']})")
        if c["warnings"]:
            clippy += "\n" + truncate("\n".join(f"[{w['category']}] {w['rendered']}" for w in c["warnings"][:25]), limit)
    u = r["unsafe"]
    unsafe = json.dumps({k: v for k, v in u["metrics"].items()}, indent=None)
    if u.get("locations"):
        unsafe += "\n" + "\n".join(u["locations"][:40])
    if not u["metrics"].get("forbid_unsafe_code"):
        unsafe += "\nNote: add `#![forbid(unsafe_code)]` at the top of src/lib.rs."
    return {"status_table": status_table(r), "integrity_feedback": integrity, "build_feedback": build,
            "test_feedback": tests, "clippy_feedback": clippy, "unsafe_feedback": unsafe}


def report_markdown(r: dict, limit: int = 12000) -> str:
    s = feedback_sections(r, limit)
    return (f"{s['status_table']}\n\n## Integrity\n{s['integrity_feedback']}\n\n## Build\n```\n{s['build_feedback']}\n```"
            f"\n\n## Tests\n{s['test_feedback']}\n\n## Clippy\n```\n{s['clippy_feedback']}\n```"
            f"\n\n## Unsafe metrics\n```\n{s['unsafe_feedback']}\n```\n")
