# env.sh - Shared environment for bash and zsh
# Sourced by both .bashrc and .zshrc
# NO SECRETS HERE - use ~/.env for API keys

# ---------- Editor ----------
export EDITOR="vim"
export VISUAL="vim"

# ---------- PATH ----------
# Local binaries
export PATH="$HOME/.local/bin:$PATH"

# Claude Code
export PATH="$HOME/.claude/bin:$PATH"

# ---------- Python (uv) ----------
# Prefer uv over pip/conda
export UV_PYTHON_PREFERENCE="managed"

# ---------- Aliases ----------
# oc is defined as a function in .zshrc.local (container-specific)
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -20'
alias gp='git push'

# safety
alias mv='mv -i'
alias cp='cp -i'

# ---------- Trash ----------
# Move files to ~/.trashcan/YYYY-MM-DD/ instead of deleting
# (~/.trash is blocked by macOS, ~/.Trash is the system Trash)
TRASHCAN="$HOME/.trashcan"

trash() {
    if [ $# -eq 0 ]; then
        echo "usage: trash <file|dir> ..." >&2
        return 1
    fi
    local trash_dir="$TRASHCAN/$(date +%Y-%m-%d)"
    mkdir -p "$trash_dir"
    local item
    for item in "$@"; do
        if [ ! -e "$item" ] && [ ! -L "$item" ]; then
            echo "trash: '$item' not found" >&2
            continue
        fi
        local name="$(basename "$item")"
        local dest="$trash_dir/$name"
        if [ -e "$dest" ]; then
            dest="${dest}.$(date +%H%M%S)"
        fi
        mv -- "$item" "$dest"
        echo "trashed: $item -> $dest"
    done
}

trash-list() {
    if [ ! -d "$TRASHCAN" ] || [ -z "$(ls -A "$TRASHCAN" 2>/dev/null)" ]; then
        echo "trash is empty"
        return
    fi
    du -sh "$TRASHCAN" | awk '{print "total: " $1}'
    echo "---"
    ls -lt "$TRASHCAN"/*/ 2>/dev/null
}

trash-empty() {
    if [ ! -d "$TRASHCAN" ]; then
        echo "trash is already empty"
        return
    fi
    if [ "$1" = "--older" ] && [ -n "$2" ]; then
        if find "$TRASHCAN" -mindepth 1 -maxdepth 1 -type d -mtime +"$2" -exec rm -rf {} +; then
            echo "removed trash older than $2 days"
        else
            echo "trash-empty: failed to remove old trash" >&2
            return 1
        fi
    else
        echo -n "empty all trash? [y/N] "
        read -r reply
        if [ "$reply" = "y" ] || [ "$reply" = "Y" ]; then
            if rm -rf "$TRASHCAN"; then
                echo "trash emptied"
            else
                echo "trash-empty: failed — check permissions" >&2
                return 1
            fi
        fi
    fi
}

# ---------- Secrets ----------
# Source local secrets if they exist
[ -f "$HOME/.env" ] && source "$HOME/.env"
