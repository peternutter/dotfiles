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
# Move files to ~/.trash/YYYY-MM-DD/ instead of deleting
# Use `trash` for recoverable deletes, `rm` stays real rm
trash() {
    if [ $# -eq 0 ]; then
        echo "usage: trash <file|dir> ..." >&2
        return 1
    fi
    local trash_dir="$HOME/.trash/$(date +%Y-%m-%d)"
    mkdir -p "$trash_dir"
    local item
    for item in "$@"; do
        if [ ! -e "$item" ] && [ ! -L "$item" ]; then
            echo "trash: '$item' not found" >&2
            continue
        fi
        local name="$(basename "$item")"
        local dest="$trash_dir/$name"
        # avoid collisions by appending timestamp
        if [ -e "$dest" ]; then
            dest="${dest}.$(date +%H%M%S)"
        fi
        mv -- "$item" "$dest"
        echo "trashed: $item -> $dest"
    done
}

# List trash contents
trash-list() {
    local trash_root="$HOME/.trash"
    if [ ! -d "$trash_root" ] || [ -z "$(ls -A "$trash_root" 2>/dev/null)" ]; then
        echo "trash is empty"
        return
    fi
    du -sh "$trash_root" | awk '{print "total: " $1}'
    echo "---"
    ls -lt "$trash_root"/*/  2>/dev/null
}

# Empty trash (all or older than N days)
trash-empty() {
    local trash_root="$HOME/.trash"
    if [ ! -d "$trash_root" ]; then
        echo "trash is already empty"
        return
    fi
    if [ "$1" = "--older" ] && [ -n "$2" ]; then
        find "$trash_root" -mindepth 1 -maxdepth 1 -type d -mtime +"$2" -exec rm -rf {} +
        echo "removed trash older than $2 days"
    else
        echo -n "empty all trash? [y/N] "
        read -r reply
        if [ "$reply" = "y" ] || [ "$reply" = "Y" ]; then
            rm -rf "$trash_root"
            echo "trash emptied"
        fi
    fi
}

# ---------- Secrets ----------
# Source local secrets if they exist
[ -f "$HOME/.env" ] && source "$HOME/.env"
