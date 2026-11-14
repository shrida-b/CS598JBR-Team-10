"""Small helpers for reading Rust source text (used by the integrity / interface checks)."""
from __future__ import annotations

import re


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
