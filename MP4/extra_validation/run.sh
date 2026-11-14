#!/usr/bin/env bash
# Extra validation beyond the CRUST-Bench tests (evaluation only; never shown to the agent).
#   bash MP4/extra_validation/run.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MP4="$(cd "$HERE/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

echo "== expr: differential test vs the original C implementation"
cc -O0 -w -I "$MP4/subjects/project_1" -o "$TMP/cdrv" "$HERE/expr_differential/c_driver.c" \
   "$MP4/subjects/project_1/mapper_expr.c" -lm
"$TMP/cdrv" "$HERE/expr_differential/cases.txt" > "$TMP/c_out.txt"
cargo +nightly-2025-05-13 build -q --manifest-path "$HERE/expr_differential/rust_driver/Cargo.toml" --target-dir "$TMP/t1"
"$TMP/t1/debug/expr_diff_driver" "$HERE/expr_differential/cases.txt" > "$TMP/rs_out.txt" 2>/dev/null
python3 "$HERE/expr_differential/compare.py" "$TMP/c_out.txt" "$TMP/rs_out.txt"

echo "== rbtree-lab: C-suite ports + randomized invariant stress"
cargo +nightly-2025-05-13 run -q --manifest-path "$HERE/rbtree_stress/Cargo.toml" --target-dir "$TMP/t2"
