#!/usr/bin/env bash
set -euo pipefail

# Dotfiles installer
# Usage: git clone <repo> ~/.dotfiles && ~/.dotfiles/install.sh
# Safe to re-run (idempotent)

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"

echo "Installing dotfiles from $DOTFILES"
echo "Detected OS: $OS"
echo ""

# ---------- Helpers ----------

link_file() {
    local src="$1" dst="$2"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -f "$dst" ]; then
        echo "  Backing up existing $dst -> ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi
    ln -s "$src" "$dst"
    echo "  Linked $dst -> $src"
}

link_dir() {
    local src="$1" dst="$2"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -d "$dst" ]; then
        echo "  Backing up existing $dst -> ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi
    ln -s "$src" "$dst"
    echo "  Linked $dst -> $src"
}

# ---------- Shell ----------
echo "==> Shell configs"
link_file "$DOTFILES/shell/.zshrc" "$HOME/.zshrc"
link_file "$DOTFILES/shell/.bashrc" "$HOME/.bashrc"

if [ ! -f "$HOME/.env" ]; then
    cp "$DOTFILES/shell/.env.example" "$HOME/.env"
    echo "  Created ~/.env from template (edit with your API keys)"
fi

# ---------- Tmux ----------
echo "==> Tmux"
link_file "$DOTFILES/tmux/.tmux.conf" "$HOME/.tmux.conf"

# ---------- Vim ----------
echo "==> Vim"
link_file "$DOTFILES/vim/.vimrc" "$HOME/.vimrc"

# ---------- Git ----------
echo "==> Git"
link_file "$DOTFILES/git/.gitconfig" "$HOME/.gitconfig"

# ---------- SSH ----------
echo "==> SSH"
mkdir -p "$HOME/.ssh/sockets"
chmod 700 "$HOME/.ssh"
link_file "$DOTFILES/ssh/config" "$HOME/.ssh/config"
chmod 600 "$HOME/.ssh/config"

# ---------- Claude Code ----------
echo "==> Claude Code"
mkdir -p "$HOME/.claude"
link_file "$DOTFILES/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"

# ---------- Oh-My-Zsh ----------
echo "==> Oh-My-Zsh"
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "  Installing oh-my-zsh..."
    RUNZSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || true
else
    echo "  Already installed"
fi

# ---------- Optional: Install utilities ----------
install_optional() {
    echo ""
    echo "==> Optional utilities"
    read -rp "Install recommended tools? (bat, eza, fd, fzf, ripgrep, htop, uv) [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        if [[ "$OS" == "Darwin" ]]; then
            if command -v brew &>/dev/null; then
                brew install bat eza fd fzf ripgrep htop uv
            else
                echo "  Homebrew not found, skipping"
            fi
        elif [[ "$OS" == "Linux" ]]; then
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y -qq bat fd-find fzf ripgrep htop
                # Install uv
                curl -LsSf https://astral.sh/uv/install.sh | sh
                # eza from cargo or binary
                if command -v cargo &>/dev/null; then
                    cargo install eza
                fi
            elif command -v apk &>/dev/null; then
                apk add --no-cache bat fd fzf ripgrep htop
                curl -LsSf https://astral.sh/uv/install.sh | sh
            fi
        fi
        echo "  Done"
    else
        echo "  Skipped"
    fi
}

install_optional

echo ""
echo "Done! Restart your shell or run: source ~/.zshrc"
echo ""
echo "Next steps:"
echo "  1. Edit ~/.env with your API keys"
echo "  2. Put machine-specific shell config in ~/.zshrc.local or ~/.bashrc.local"
