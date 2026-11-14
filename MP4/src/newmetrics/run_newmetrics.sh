#!/usr/bin/env bash
# Run the instructional team's NewMetrics unsafe-metrics tool on one crate.
#   bash src/newmetrics/run_newmetrics.sh <crate_dir> [summary.json] [artifacts_dir]
# NewMetrics also writes decls.txt / derefs.txt / unsafe_spans.txt into the crate; they are
# moved to [artifacts_dir] if given, otherwise removed, so the translation stays clean.
# Requires: cargo install --debug --locked --path <course repo>/MP4/newmetrics --force
# aggregate.py is an unmodified copy of the course's MP4/newmetrics/aggregate.py
# (Intelligent-CAT-Lab/CS598JBR-Team-0, commit 4597e75). Prints the summary JSON on stdout.
set -euo pipefail
CRATE="${1:?usage: run_newmetrics.sh <crate_dir> [summary.json]}"
OUT="${2:-/dev/null}"
ART="${3:-}"
case "$OUT" in /*|/dev/null) ;; *) OUT="$PWD/$OUT" ;; esac
[ -n "$ART" ] && { mkdir -p "$ART"; ART="$(cd "$ART" && pwd)"; }
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v cargo-newmetrics >/dev/null || { echo "cargo-newmetrics not installed" >&2; exit 3; }
cd "$CRATE"
cargo +nightly-2025-05-13 newmetrics 2>&1 | python3 "$HERE/aggregate.py" --out "$OUT"
for f in decls.txt derefs.txt unsafe_spans.txt; do
  [ -f "$f" ] || continue
  if [ -n "$ART" ]; then mv "$f" "$ART/$f"; else rm -f "$f"; fi
done
