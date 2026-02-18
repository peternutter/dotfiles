#!/usr/bin/env bash
set -euo pipefail

# Dotfiles installer
# Usage: git clone <repo> ~/.dotfiles && ~/.dotfiles/install.sh [flags]
# Flags:
#   --nvim       Install Neovim/LazyVim config
#   --tools      Install recommended CLI tools (bat, eza, fd, fzf, ripgrep, htop, uv)
#   --all        Install everything
# Safe to re-run (idempotent)

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"

# Parse flags
INSTALL_NVIM=false
INSTALL_TOOLS=false
for arg in "$@"; do
    case "$arg" in
        --nvim)  INSTALL_NVIM=true ;;
        --tools) INSTALL_TOOLS=true ;;
        --all)   INSTALL_NVIM=true; INSTALL_TOOLS=true ;;
    esac
done

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
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
    ssh-keygen -t ed25519 -C "peternutter100@gmail.com" -f "$HOME/.ssh/id_ed25519" -N ""
    echo "  Generated ~/.ssh/id_ed25519"
    echo "  Public key:"
    cat "$HOME/.ssh/id_ed25519.pub"
else
    echo "  SSH key already exists, skipping"
fi

# ---------- Claude Code ----------
echo "==> Claude Code"
mkdir -p "$HOME/.claude"
link_file "$DOTFILES/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"
# Merge MCP servers into ~/.claude.json (Claude Code reads user MCPs from there)
if command -v jq &>/dev/null; then
    if [ ! -f "$HOME/.claude.json" ]; then
        echo '{}' > "$HOME/.claude.json"
    fi
    for server in $(jq -r '.mcpServers | keys[]' "$DOTFILES/claude/.mcp.json"); do
        if jq -e ".mcpServers.\"$server\"" "$HOME/.claude.json" >/dev/null 2>&1; then
            echo "  Skipped MCP server '$server' (already configured)"
        else
            SERVER_CONFIG=$(jq ".mcpServers.\"$server\"" "$DOTFILES/claude/.mcp.json" \
                | jq 'walk(if type == "string" and test("^\\$\\{.+\\}$") then (capture("\\$\\{(?<v>.+)\\}") | .v | $ENV[.]) // . else . end)')
            jq --arg name "$server" --argjson config "$SERVER_CONFIG" \
                '.mcpServers[$name] = $config' "$HOME/.claude.json" > "$HOME/.claude.json.tmp" \
                && mv -f "$HOME/.claude.json.tmp" "$HOME/.claude.json"
            echo "  Added MCP server '$server'"
        fi
    done
else
    echo "  WARNING: jq not found, skipping MCP server config (install jq and re-run)"
fi
link_file "$DOTFILES/claude/statusline.sh" "$HOME/.claude/statusline.sh"
link_dir "$DOTFILES/claude/output-styles" "$HOME/.claude/output-styles"

# ---------- Oh-My-Zsh ----------
echo "==> Oh-My-Zsh"
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "  Installing oh-my-zsh..."
    RUNZSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || true
else
    echo "  Already installed"
fi

# ---------- Optional: Neovim (LazyVim) ----------
if [ "$INSTALL_NVIM" = true ]; then
    echo "==> Neovim config (LazyVim)"
    mkdir -p "$HOME/.config"
    link_dir "$DOTFILES/nvim" "$HOME/.config/nvim"
fi

# ---------- Optional: Install utilities ----------
if [ "$INSTALL_TOOLS" = true ]; then
    echo "==> Installing CLI tools"
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
            curl -LsSf https://astral.sh/uv/install.sh | sh
        elif command -v apk &>/dev/null; then
            apk add --no-cache bat fd fzf ripgrep htop
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
    fi
fi

echo ""
echo "Done! Restart your shell or run: source ~/.zshrc"
echo ""
echo "Next steps:"
echo "  1. Edit ~/.env with your API keys"
echo "  2. Put machine-specific config in ~/.zshrc.local or ~/.bashrc.local"
echo ""
echo "To change configs across all machines, edit files in this repo and push."
echo "Local symlinks will pick up changes automatically."
