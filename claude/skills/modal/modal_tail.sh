#!/usr/bin/env bash
# modal_tail.sh -- re-attach to a running detached app's live logs.
#
# Use when the launch window (modal_launch.sh) died but the --detach app is still running,
# or from any other pod. `modal app logs` follows by default.
#
# Usage:  modal_tail.sh [app-name]
#   no arg -> lists running apps to pick from.
set -euo pipefail
if [ $# -ge 1 ]; then exec modal app logs "$1"; fi
echo "running apps:"; modal app list 2>/dev/null | cat
echo; echo "tail one with:  modal_tail.sh <app-name>   (or: modal app logs <app-name>)"
