#!/usr/bin/env bash
# Rebuild generated pages. Run from anywhere:
#
#   bash tools/build.sh          # rebuild pages from committed derived data
#   bash tools/build.sh --all    # also recompute from raw material in ../source/
#
# Stages marked [raw] need uncommitted source material. On a machine without it, use the
# default: every page rebuilds from the aggregate files in tools/derived/.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
ALL=${1:-}

run () { echo; echo "==> $1"; shift; "$@"; }

if [ "$ALL" = "--all" ]; then
  : # run "[raw] compute something" $PY compute_something.py
fi

: # run "pages: x" $PY build_x.py

echo
echo "==> done. public/index.html is hand-maintained and is not generated."
