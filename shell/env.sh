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
if command -v opencode >/dev/null 2>&1; then
    alias oc='opencode .'
fi
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
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'

# ---------- Secrets ----------
# Source local secrets if they exist
[ -f "$HOME/.env" ] && source "$HOME/.env"
