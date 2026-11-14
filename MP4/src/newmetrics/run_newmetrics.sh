#!/usr/bin/env bash
# Run the instructional team's NewMetrics unsafe-metrics tool on one crate.
#   bash src/newmetrics/run_newmetrics.sh <crate_dir> [summary.json]
# Requires: cargo install --debug --locked --path <course repo>/MP4/newmetrics --force
# aggregate.py is an unmodified copy of the course's MP4/newmetrics/aggregate.py
# (Intelligent-CAT-Lab/CS598JBR-Team-0, commit 4597e75). Prints the summary JSON on stdout.
set -euo pipefail
CRATE="${1:?usage: run_newmetrics.sh <crate_dir> [summary.json]}"
OUT="${2:-/dev/null}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v cargo-newmetrics >/dev/null || { echo "cargo-newmetrics not installed" >&2; exit 3; }
cd "$CRATE"
cargo +nightly-2025-05-13 newmetrics 2>&1 | python3 "$HERE/aggregate.py" --out "$OUT"
