#!/usr/bin/env bash
# Reproduce the MP4 pipeline on one assigned project, end to end.
#
#   bash MP4/src/reproduce.sh project_1          # expr
#   bash MP4/src/reproduce.sh project_2          # rbtree-lab
#   bash MP4/src/reproduce.sh project_1 --fresh  # discard previous run first
#
# Steps: environment check -> agentic translation loop (resumes automatically if
# a previous run paused on the free-tier quota) -> grader-style evaluation.
set -euo pipefail

PROJECT="${1:?usage: reproduce.sh project_1|project_2 [--fresh] [extra run_pipeline.py args]}"
shift
MP4_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MP4_DIR"
TOOLCHAIN="nightly-2025-05-13"

echo "== 1. environment check"
python3 src/check_setup.py --no-network

echo "== 2. agentic translation pipeline"
python3 src/run_pipeline.py --project "$PROJECT" "$@"

OUT="$(python3 -c "import tomllib;print(tomllib.load(open('configs/projects.toml','rb'))['$PROJECT']['output_dir'])")"
echo "== 3. grader-style evaluation of $OUT"
cd "$MP4_DIR/$OUT"
cargo +"$TOOLCHAIN" build
cargo +"$TOOLCHAIN" test || true
cargo +"$TOOLCHAIN" clippy --all-targets --all-features -- \
    -W clippy::correctness -W clippy::style -W clippy::complexity -W clippy::perf || true
python3 "$MP4_DIR/src/unsafe_metrics.py" . | python3 -c "import json,sys;print(json.dumps(json.load(sys.stdin)['metrics'],indent=1))"
echo "Trajectory summary: $MP4_DIR/trajectories/$PROJECT/TRAJECTORY.md"
