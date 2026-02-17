# .bashrc - Bash configuration
# Portable across macOS and Linux

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# ---------- History ----------
HISTCONTROL=ignoreboth
HISTSIZE=10000
HISTFILESIZE=20000
shopt -s histappend

# ---------- Shell options ----------
shopt -s checkwinsize
shopt -s globstar 2>/dev/null

# ---------- Prompt ----------
# Simple but informative prompt: user@host:dir$
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# ---------- Shared env ----------
DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
[ -f "$DOTFILES_DIR/env.sh" ] && source "$DOTFILES_DIR/env.sh"
# Fallback: source from home if symlinked
[ -f "$HOME/.dotfiles/shell/env.sh" ] && source "$HOME/.dotfiles/shell/env.sh"

# ---------- Platform-specific ----------
if [[ "$(uname)" == "Darwin" ]]; then
    [ -f /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ---------- Local overrides ----------
[ -f "$HOME/.bashrc.local" ] && source "$HOME/.bashrc.local"

[ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"
