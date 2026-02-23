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
# Resolve symlinks to find the real script directory
_bashrc_path="${BASH_SOURCE[0]}"
if [ -L "$_bashrc_path" ]; then
    if command -v realpath &>/dev/null; then
        _bashrc_path="$(realpath "$_bashrc_path")"
    elif command -v greadlink &>/dev/null; then
        _bashrc_path="$(greadlink -f "$_bashrc_path")"
    fi
fi
DOTFILES_DIR="$(cd "$(dirname "$_bashrc_path")" 2>/dev/null && pwd)"
unset _bashrc_path
[ -f "$DOTFILES_DIR/env.sh" ] && source "$DOTFILES_DIR/env.sh"

# ---------- Platform-specific ----------
if [[ "$(uname)" == "Darwin" ]]; then
    [ -f /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ---------- Local overrides ----------
[ -f "$HOME/.bashrc.local" ] && source "$HOME/.bashrc.local"

[ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"
