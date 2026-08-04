#!/usr/bin/env bash
# modal_status.sh -- ONE view over a sweep's jobs: state + last log line per job.
# States (grep-based, override via env): ERROR / DONE / RUNNING (client alive) / DETACHED
# (client gone but no done-marker -- the app may still run server-side: modal app logs -f).
#
# Usage: modal_status.sh <sweep-name> [--watch]     # --watch = refresh every 30s (run in ONE tmux window)
# Env:   DONE_RE / ERR_RE  override the default completion/error regexes.
set -euo pipefail
# User-level skill: derive the repo from cwd (or $MATS_REPO), not from this file's location.
REPO="${MATS_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || echo /workspace/mats_project)}"
[ $# -ge 1 ] || { echo "usage: modal_status.sh <sweep-name> [--watch]"; ls "$REPO/logs/modal" 2>/dev/null; exit 2; }
SWEEP="$1"
DIR="$REPO/logs/modal/$SWEEP"
DONE_RE="${DONE_RE:-train_runtime|=== eval done|App completed|### done}"
ERR_RE="${ERR_RE:-Traceback|SystemExit|CUDA out of memory|NotFoundError|BadRequestError|Error code: [45]}"

show() {
  echo "== sweep $SWEEP  ($(date -u +%H:%M:%SZ)) =="
  # any *.log in the sweep dir counts, manifest or not (covers hand-launched jobs)
  for LOG in "$DIR"/*.log; do
    [ -e "$LOG" ] || { echo "(no logs in $DIR)"; break; }
    NAME="$(basename "$LOG" .log)"
    ST=RUNNING; ERR=0; DON=0
    grep -qE "$ERR_RE"  "$LOG" && ERR=1
    grep -qE "$DONE_RE" "$LOG" && DON=1
    [ $ERR = 1 ] && ST=ERROR
    [ $DON = 1 ] && { ST=DONE; [ $ERR = 1 ] && ST='DONE+ERR'; }   # finished, but errors in log -> inspect
    if [ "$ST" = RUNNING ]; then
      PID="$(cat "$DIR/$NAME.pid" 2>/dev/null || true)"
      { [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; } || fuser "$LOG" >/dev/null 2>&1 || ST=DETACHED
    fi
    printf '%-10s %-24s %s\n' "$ST" "$NAME" "$(tail -c 400 "$LOG" | tr '\n' ' ' | tail -c 110)"
  done
}
if [ "${2:-}" = "--watch" ]; then while true; do clear; show; sleep 30; done; else show; fi
