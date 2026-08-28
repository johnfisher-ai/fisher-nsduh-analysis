#!/usr/bin/env bash
#   bash tools/build.sh          # pages, from committed derived data
#   bash tools/build.sh --all    # also recompute from the NSDUH files (~1.1 GB, not committed)
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
run () { echo; echo "==> $1"; shift; "$@"; }
if [ "${1:-}" = "--all" ]; then
  run "[raw] pool, weight, model, design effects" $PY compute_analysis.py
  run "[raw] figures"                             $PY make_figures.py
  run "      Colab notebook (synthetic)"          $PY make_notebook.py
fi
run "pages" $PY build_pages.py
echo; echo "==> done."
