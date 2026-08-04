#!/usr/bin/env bash
# modal_batch.sh -- launch a FLEET of detached Modal jobs into ONE sweep folder, NO tmux
# window per job (Peter, 2026-07-23: sweeps get per-job logs + one monitor, not N windows).
#
# Each job line = "<job-name> <modal-run args...>". The client stream goes to
# logs/modal/<sweep>/<job-name>.log; --detach means the app survives even if the client dies
# (re-tail: modal app logs -f). A manifest.tsv records job -> log for modal_status.sh.
#
# Usage:
#   modal_batch.sh <sweep-name> <jobs-file>
#   ... | modal_batch.sh <sweep-name> -          # job lines on stdin
# Example jobs-file line:
#   aw-s1  examples/train_olmo_modal.py::main --experiment experiments/sdf/x.yaml --run aw --seed 1 --gpu B300
# Monitor: modal_status.sh <sweep-name> [--watch]
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: modal_batch.sh <sweep-name> <jobs-file|->"; exit 2; }
SWEEP="$1"; SRC="$2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# User-level skill: derive the repo from cwd (or $MATS_REPO), not from this file's location.
REPO="${MATS_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || echo /workspace/mats_project)}"
DIR="$REPO/logs/modal/$SWEEP"; mkdir -p "$DIR"

n=0
while read -r NAME ARGS; do
  [ -z "$NAME" ] && continue; case "$NAME" in \#*) continue;; esac
  LOG="$DIR/$NAME.log"
  # nohup: the client process survives this shell; --detach: the APP survives the client.
  ( cd "$HERE" && nohup modal run --detach $ARGS >"$LOG" 2>&1 & echo "$!" >"$DIR/$NAME.pid" )
  printf '%s\t%s\n' "$NAME" "$LOG" >> "$DIR/manifest.tsv"
  echo "launched $NAME -> $LOG"; n=$((n+1))
done < <(cat "$([ "$SRC" = - ] && echo /dev/stdin || echo "$SRC")")
echo "== $n jobs launched into $DIR; monitor: modal_status.sh $SWEEP --watch =="
