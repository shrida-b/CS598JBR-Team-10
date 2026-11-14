#!/usr/bin/env python3
"""Compare C reference vs Rust translation outputs for expr (see run.sh)."""
import sys

def load(fn):
    rows = []
    for line in open(fn).read().splitlines():
        if line.split("|")[0] in ("f", "i", "fi", "if") and line.count("|") >= 2:
            rows.append(line)
        elif rows:                       # error messages printed by the parsers
            rows[-1] += " " + line
    return rows

def close(a, b):
    if a == b:
        return True
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) <= 1e-6 * max(1, abs(fa)) or (fa != fa and fb != fb)
    except ValueError:
        return False

c, r = load(sys.argv[1]), load(sys.argv[2])
agree, differ = 0, []
for cl, rl in zip(c, r):
    mode, ex, cv = cl.split("|", 2)
    rv = rl.split("|", 2)[2]
    if "PARSEFAIL" in cv or "PANIC-ON-PARSE" in rv:
        print(f"  invalid/edge input {ex!r:24} C: {cv.split()[0] if cv.split() else cv:10} Rust: {rv.strip()}")
        continue
    cvals, rvals = cv.split()[0].strip(";").split(";"), rv.split()[0].strip(";").split(";")
    if len(cvals) == len(rvals) and all(close(a, b) for a, b in zip(cvals, rvals)):
        agree += 1
    else:
        differ.append(f"  DIFF [{mode}] {ex}: C={cv} Rust={rv}")
print(f"{agree} valid expressions agree, {len(differ)} differ")
print("\n".join(differ))
