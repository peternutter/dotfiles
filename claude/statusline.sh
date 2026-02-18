#!/usr/bin/env bash
# Claude Code status line — shows project, git branch, and context usage
data=$(cat)

model=$(echo "$data" | jq -r '.model.display_name // "?"')
project=$(echo "$data" | jq -r '.workspace.project_dir // .cwd // "~"' | xargs basename)
ctx=$(echo "$data" | jq -r '.context_window.used_percentage // 0')
cost=$(echo "$data" | jq -r '.cost.total_cost_usd // 0' | xargs printf '$%.2f')

# Git branch (cached for 5s to avoid slowdown)
cache="/tmp/claude-statusline-git"
if [ ! -f "$cache" ] || [ "$(( $(date +%s) - $(stat -c %Y "$cache" 2>/dev/null || stat -f %m "$cache" 2>/dev/null || echo 0) ))" -gt 5 ]; then
    branch=$(git -C "$(echo "$data" | jq -r '.workspace.project_dir // "."')" branch --show-current 2>/dev/null || echo "")
    echo "$branch" > "$cache"
else
    branch=$(cat "$cache")
fi

# Build status line
parts=()
parts+=("$model")
parts+=("$project")
[ -n "$branch" ] && parts+=("$branch")
parts+=("ctx:${ctx}%")
parts+=("$cost")

echo "${parts[*]}" | sed 's/ / │ /g'
