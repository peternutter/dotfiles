# .zshrc - Zsh configuration
# Portable across macOS and Linux

# ---------- Oh-My-Zsh ----------
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)

# Install oh-my-zsh if missing
if [ -d "$ZSH" ]; then
    source "$ZSH/oh-my-zsh.sh"
fi

# ---------- Vi mode ----------
bindkey -v

# ---------- Completions ----------
autoload -Uz compinit
compinit

# ---------- History ----------
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS

# ---------- Shared env ----------
DOTFILES_DIR="$(dirname "$(readlink -f "${(%):-%x}" 2>/dev/null || echo "$HOME/.dotfiles/shell/.zshrc")")"
[ -f "$DOTFILES_DIR/env.sh" ] && source "$DOTFILES_DIR/env.sh"
# Fallback: source from home if symlinked
[ -f "$HOME/.dotfiles/shell/env.sh" ] && source "$HOME/.dotfiles/shell/env.sh"

# ---------- Platform-specific ----------
if [[ "$(uname)" == "Darwin" ]]; then
    # Homebrew
    [ -f /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ---------- Local overrides ----------
# Put machine-specific config in ~/.zshrc.local
[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"
