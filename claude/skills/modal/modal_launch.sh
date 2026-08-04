#!/usr/bin/env bash
# modal_launch.sh -- launch a Modal app in a NEW tmux window, detached + live-tailing.
#
# Why this exists: on Modal there is no pod to attach to. `modal run` is a *client*
# that streams the remote container's logs to your terminal; if that client exits, an
# ephemeral app is STOPPED (modal-docs L2382). `--detach` keeps the app alive server-side
# after the client exits (L2385) while still streaming live. So the durable "launch it in
# a window I can tail" pattern is: run `modal run --detach` inside a tmux window (survives),
# teeing to a log on the shared volume (re-attachable). If the window dies, the run keeps
# going; re-tail with `modal app logs -f <app>` (see modal_tail.sh).
#
# Peter is ALWAYS already inside tmux (project rule) -> we add a WINDOW to the current
# session, never `tmux new-session`. Ctrl-b w lists the windows; each seed gets its own.
#
# Usage:
#   modal_launch.sh <window-name> <app.py[::entrypoint]> [extra modal-run args...]
# Examples:
#   modal_launch.sh olmo-b200 examples/olmo32b_fit_smoke.py --gpu B200 --stage fit
#   modal_launch.sh seed3     train_olmo.py::main --seed 3
#
# Env:
#   MODAL_LOG_DIR   where to tee logs (default: <repo>/logs/modal/<MODAL_SWEEP:-adhoc>)
#   MODAL_SWEEP     sweep/topic name grouping logs into one folder (Peter, 2026-07-23:
#                   logs live under gitignored logs/modal/<sweep>/, NOT in notes/)
set -euo pipefail

[ $# -ge 2 ] || { echo "usage: modal_launch.sh <window-name> <app.py[::entry]> [args...]"; exit 2; }
NAME="$1"; shift
TARGET="$1"; shift

[ -n "${TMUX:-}" ] || { echo "ERROR: not inside tmux. Start/attach a tmux session first."; exit 1; }
SESSION="$(tmux display-message -p '#S')"

# Default log dir = gitignored logs/modal/<sweep>/ at repo root (never in notes/).
# This skill is user-level (~/.claude/skills), so derive the repo from cwd, not from $0.
REPO="${MATS_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || echo /workspace/mats_project)}"
LOGDIR="${MODAL_LOG_DIR:-$REPO/logs/modal/${MODAL_SWEEP:-adhoc}}"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/${NAME}.log"

# --detach: run survives the window; live stream still shows in the window + tee to NFS.
RUN="modal run --detach $(printf '%q ' "$TARGET" "$@")"
tmux new-window -t "$SESSION" -n "$NAME" \
  "echo '== $RUN =='; $RUN 2>&1 | tee '$LOG'; echo; echo '[run client exited -- app may still be running detached; press enter to close]'; read"

echo "launched '$NAME' in tmux session '$SESSION'"
echo "  window : Ctrl-b w  (or: tmux select-window -t '$SESSION:$NAME')"
echo "  log    : $LOG"
echo "  re-tail: modal app logs -f <app-name>   (survives if this window dies)"
