# dotfiles

Portable terminal configs for macOS and Linux. Works in containers, VMs, and SSH sessions.

## Quick Install

```bash
git clone https://github.com/peternutter/dotfiles.git ~/.dotfiles
~/.dotfiles/install.sh
```

With optional extras:
```bash
~/.dotfiles/install.sh --nvim       # include Neovim/LazyVim
~/.dotfiles/install.sh --tools      # install CLI tools (bat, eza, fd, fzf, ripgrep, htop, uv)
~/.dotfiles/install.sh --all        # everything
```

## What's Included

| Config | What it does |
|--------|-------------|
| **shell** | Shared env vars, aliases, PATH for both bash and zsh |
| **zsh** | Oh-my-zsh, vi mode, history |
| **bash** | Clean prompt, history, same env as zsh |
| **tmux** | C-Space prefix, vim navigation, mouse scroll, catppuccin, OSC 52 clipboard |
| **vim** | OSC 52 clipboard (yank works over SSH), relative line numbers, sane defaults |
| **git** | Aliases, rebase on pull, auto setup remote |
| **ssh** | Generates ed25519 key if missing |
| **nvim** | LazyVim setup (`--nvim` flag) |
| **claude** | Claude Code global instructions, settings, and MCP templates |

## How It Works

Configs are symlinked from `~/.dotfiles/` to your home directory. This means:

- **To change something on all machines**: edit files in this repo, commit, and push. Every machine with the symlinks picks up changes on `git pull`.
- **To change something on one machine only**: put it in `~/.zshrc.local` or `~/.bashrc.local`.
- **API keys and secrets**: go in `~/.env` (never committed). See `shell/.env.example` for the template.

## Local Overrides

Machine-specific config goes in:
- `~/.zshrc.local` — extra PATH entries, machine-specific exports
- `~/.bashrc.local` — same for bash
- `~/.env` — API keys and secrets (gitignored)

## MCP Servers (Claude + OpenCode)

The MCP server list lives in `dotfiles/claude/.mcp.json`. The dotfiles installer merges
that list into both:

- Claude Code: `~/.claude.json` (key: `mcpServers`)
- OpenCode: `~/.config/opencode/opencode.json` (key: `mcp`)

When adding a new MCP server, update `dotfiles/claude/.mcp.json` and re-run
`dotfiles/install.sh` (or rebuild the claude-code container).

## OpenCode Vim

OpenCode does not support Vim/vi keybinding mode in its TUI input editor.
`EDITOR`/`VISUAL` are set to `vim` for external editor usage, but in-app
keybindings remain OpenCode defaults.
