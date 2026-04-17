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

resolve_command() {
    local cmd="$1"
    local resolved
    resolved=$(command -v "$cmd" 2>/dev/null || true)
    if [ -n "$resolved" ]; then
        echo "$resolved"
        return
    fi
    if [ -x "$HOME/.local/bin/$cmd" ]; then
        echo "$HOME/.local/bin/$cmd"
        return
    fi
    echo "$cmd"
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
# zdiff3 requires git >= 2.35; downgrade to diff3 on older systems
GIT_VER=$(git --version | sed 's/[^0-9.]*//' | cut -d' ' -f1)
GIT_MAJOR=$(echo "$GIT_VER" | cut -d. -f1)
GIT_MINOR=$(echo "$GIT_VER" | cut -d. -f2)
if [ "${GIT_MAJOR:-0}" -lt 2 ] || { [ "${GIT_MAJOR:-0}" -eq 2 ] && [ "${GIT_MINOR:-0}" -lt 35 ]; }; then
    git config --global merge.conflictstyle diff3
    echo "  git $GIT_VER: zdiff3 unsupported, using diff3"
fi

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
MCP_SOURCE="$DOTFILES/claude/.mcp.json"
mkdir -p "$HOME/.claude"
link_file "$DOTFILES/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"

echo "==> Codex"
mkdir -p "$HOME/.codex"
link_file "$DOTFILES/claude/CLAUDE.md" "$HOME/.codex/AGENTS.md"
# Codex ships bundled skills in ~/.codex/skills/.system/ and ~/.codex/skills/codex-primary-runtime/,
# so we link each of our skills as a sibling rather than replacing the whole directory.
mkdir -p "$HOME/.codex/skills"
for skill_dir in "$DOTFILES/claude/skills"/*; do
    [ -d "$skill_dir" ] || continue
    link_file "$skill_dir" "$HOME/.codex/skills/$(basename "$skill_dir")"
done
# Merge MCP servers into ~/.claude.json (Claude Code reads user MCPs from there)
if command -v jq &>/dev/null; then
    if [ ! -f "$HOME/.claude.json" ]; then
        echo '{}' > "$HOME/.claude.json"
    fi
    for server in $(jq -r '.mcpServers | keys[]' "$MCP_SOURCE"); do
        if jq -e ".mcpServers.\"$server\"" "$HOME/.claude.json" >/dev/null 2>&1; then
            echo "  Skipped MCP server '$server' (already configured)"
        else
            SERVER_CONFIG=$(jq ".mcpServers.\"$server\"" "$MCP_SOURCE" \
                | jq 'walk(if type == "string" and test("^\\$\\{.+\\}$") then (capture("\\$\\{(?<v>.+)\\}") | .v | $ENV[.]) // . else . end)')
            # Resolve command to absolute path so MCP subprocesses find it
            CMD=$(echo "$SERVER_CONFIG" | jq -r '.command')
            RESOLVED_CMD=$(resolve_command "$CMD")
            SERVER_CONFIG=$(echo "$SERVER_CONFIG" | jq --arg cmd "$RESOLVED_CMD" '.command = $cmd')
            jq --arg name "$server" --argjson config "$SERVER_CONFIG" \
                '.mcpServers[$name] = $config' "$HOME/.claude.json" > "$HOME/.claude.json.tmp" \
                && mv -f "$HOME/.claude.json.tmp" "$HOME/.claude.json"
            echo "  Added MCP server '$server'"
        fi
    done

    # Enable remote control WebSocket server on every session
    if ! jq -e '.remoteControlAtStartup' "$HOME/.claude.json" >/dev/null 2>&1; then
        jq '.remoteControlAtStartup = true' "$HOME/.claude.json" > "$HOME/.claude.json.tmp" \
            && mv -f "$HOME/.claude.json.tmp" "$HOME/.claude.json"
        echo "  Enabled remoteControlAtStartup"
    fi

    echo "==> OpenCode MCP"
    OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
    OPENCODE_CONFIG="$OPENCODE_CONFIG_DIR/opencode.json"
    mkdir -p "$OPENCODE_CONFIG_DIR"
    if [ ! -f "$OPENCODE_CONFIG" ]; then
        echo '{}' > "$OPENCODE_CONFIG"
    fi

    # Global instructions: OpenCode reads ~/.claude/CLAUDE.md natively via its
    # Claude Code compatibility fallback, so no opencode.json wiring is needed.

    for server in $(jq -r '.mcpServers | keys[]' "$MCP_SOURCE"); do
        SERVER_CONFIG=$(jq ".mcpServers.\"$server\"" "$MCP_SOURCE" \
            | jq 'walk(if type == "string" and test("^\\$\\{.+\\}$") then (capture("\\$\\{(?<v>.+)\\}") | .v | $ENV[.]) // . else . end)')
        CMD=$(echo "$SERVER_CONFIG" | jq -r '.command')
        RESOLVED_CMD=$(resolve_command "$CMD")
        OPENCODE_SERVER=$(echo "$SERVER_CONFIG" | jq --arg cmd "$RESOLVED_CMD" \
            '{
                type: "local",
                command: ([$cmd] + (.args // [])),
                environment: (.env // .environment // {})
            }')
        if jq -e ".mcp.\"$server\"" "$OPENCODE_CONFIG" >/dev/null 2>&1; then
            CURRENT_CMD=$(jq -r ".mcp.\"$server\".command[0] // empty" "$OPENCODE_CONFIG")
            if [ -n "$CURRENT_CMD" ] && [ "$CURRENT_CMD" != "$RESOLVED_CMD" ]; then
                jq --arg name "$server" --argjson config "$OPENCODE_SERVER" \
                    '.mcp[$name] = $config' "$OPENCODE_CONFIG" > "$OPENCODE_CONFIG.tmp" \
                    && mv -f "$OPENCODE_CONFIG.tmp" "$OPENCODE_CONFIG"
                echo "  Updated MCP server '$server' for OpenCode"
            else
                echo "  Skipped MCP server '$server' (already configured for OpenCode)"
            fi
        else
            jq --arg name "$server" --argjson config "$OPENCODE_SERVER" \
                '.mcp[$name] = $config' "$OPENCODE_CONFIG" > "$OPENCODE_CONFIG.tmp" \
                && mv -f "$OPENCODE_CONFIG.tmp" "$OPENCODE_CONFIG"
            echo "  Added MCP server '$server' to OpenCode"
        fi
    done

    echo "==> Codex MCP"
    CODEX_CONFIG_DIR="$HOME/.codex"
    CODEX_CONFIG="$CODEX_CONFIG_DIR/config.toml"
    mkdir -p "$CODEX_CONFIG_DIR"
    if [ ! -f "$CODEX_CONFIG" ]; then
        touch "$CODEX_CONFIG"
    fi

    # Build a JSON payload of the desired Codex mcp_servers entries.
    CODEX_MCP_JSON=$(jq -c '.mcpServers' "$MCP_SOURCE" \
        | jq 'walk(if type == "string" and test("^\\$\\{.+\\}$") then (capture("\\$\\{(?<v>.+)\\}") | .v | $ENV[.]) // . else . end)' \
        | jq -c 'to_entries
            | map({
                name: .key,
                command: (.value.command // ""),
                args: (.value.args // []),
                env: (.value.env // .value.environment // {})
            })')

    if ! command -v python3 >/dev/null 2>&1; then
        echo "  WARNING: python3 not found; cannot update $CODEX_CONFIG"
    else
        python3 - "$CODEX_CONFIG" "$CODEX_MCP_JSON" <<'PY'
import json
import re
import shutil
import os
import sys

config_path = sys.argv[1]
servers = json.loads(sys.argv[2])

server_names = {s["name"] for s in servers}

def resolve_command(cmd: str) -> str:
    if not cmd:
        return cmd
    resolved = shutil.which(cmd)
    if resolved:
        return resolved
    local = os.path.expanduser(f"~/.local/bin/{cmd}")
    if os.path.isfile(local) and os.access(local, os.X_OK):
        return local
    return cmd

header_re = re.compile(r'^\[(?P<table>[^\]]+)\]\s*$')

with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
skip = False
skip_managed = False
for line in lines:
    stripped = line.strip()

    if stripped == '# --- dotfiles managed: MCP servers (do not edit by hand) ---':
        skip_managed = True
        continue
    if stripped == '# --- end dotfiles managed MCP servers ---':
        skip_managed = False
        continue
    if skip_managed:
        continue

    m = header_re.match(stripped)
    if m:
        table = m.group('table')
        if table.startswith('mcp_servers.'):
            rest = table[len('mcp_servers.'):]
            name = rest.split('.', 1)[0]
            skip = name in server_names
        else:
            skip = False

    if not skip:
        out.append(line)

def toml_quote(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

def toml_array(items):
    return '[' + ', '.join(toml_quote(x) for x in items) + ']'

block = []
block.append('\n# --- dotfiles managed: MCP servers (do not edit by hand) ---\n')

placeholder_re = re.compile(r'^\$\{.+\}$')
for s in servers:
    name = s['name']
    command = resolve_command(s.get('command') or '')
    args = s.get('args') or []
    env = s.get('env') or {}

    # Resolve empty/invalid entries defensively.
    if not name or not command:
        continue

    block.append(f"[mcp_servers.{name}]\n")
    block.append(f"command = {toml_quote(command)}\n")
    block.append(f"args = {toml_array(args)}\n")

    env_items = [(k, v) for k, v in env.items() if isinstance(k, str) and isinstance(v, str) and v and not placeholder_re.match(v)]
    if env_items:
        block.append(f"\n[mcp_servers.{name}.env]\n")
        for k, v in sorted(env_items):
            block.append(f"{k} = {toml_quote(v)}\n")

    block.append("\n")

block.append('# --- end dotfiles managed MCP servers ---\n')

with open(config_path, 'w', encoding='utf-8') as f:
    f.writelines(out)
    f.writelines(block)
PY
        echo "  Synced MCP servers into $CODEX_CONFIG"
    fi
else
    echo "  WARNING: jq not found, skipping MCP server config (install jq and re-run)"
fi
link_file "$DOTFILES/claude/statusline.sh" "$HOME/.claude/statusline.sh"
link_dir "$DOTFILES/claude/output-styles" "$HOME/.claude/output-styles"
link_dir "$DOTFILES/claude/skills" "$HOME/.claude/skills"

# ---------- Oh-My-Zsh ----------
echo "==> Oh-My-Zsh"
if ! command -v zsh &>/dev/null; then
    echo "  zsh not found, installing..."
    if [[ "$OS" == "Linux" ]]; then
        if [ "$(id -u)" -eq 0 ]; then
            apt-get update -qq && apt-get install -y -qq zsh
        else
            sudo apt-get update -qq && sudo apt-get install -y -qq zsh
        fi
    elif [[ "$OS" == "Darwin" ]] && command -v brew &>/dev/null; then
        brew install zsh
    else
        echo "  WARNING: cannot install zsh automatically, install it manually"
    fi
fi
if ! command -v tmux &>/dev/null; then
    echo "  tmux not found, installing..."
    if [[ "$OS" == "Linux" ]]; then
        if [ "$(id -u)" -eq 0 ]; then
            apt-get update -qq && apt-get install -y -qq tmux
        else
            sudo apt-get update -qq && sudo apt-get install -y -qq tmux
        fi
    elif [[ "$OS" == "Darwin" ]] && command -v brew &>/dev/null; then
        brew install tmux
    fi
fi
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
        # Use sudo only if not root
        SUDO=""
        [ "$(id -u)" -ne 0 ] && SUDO="sudo"
        if command -v apt-get &>/dev/null; then
            $SUDO apt-get update -qq
            $SUDO apt-get install -y -qq bat fd-find fzf ripgrep htop jq
            curl -LsSf https://astral.sh/uv/install.sh | sh
        elif command -v apk &>/dev/null; then
            $SUDO apk add --no-cache bat fd fzf ripgrep htop jq
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
