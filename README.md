# dotfiles

Portable terminal configs for macOS and Linux. Works in containers, VMs, and SSH sessions.

## Quick Install

```bash
git clone https://github.com/peternutter/dotfiles.git ~/.dotfiles
~/.dotfiles/install.sh
```

Or one-liner for containers:
```bash
bash <(curl -sL https://raw.githubusercontent.com/peternutter/dotfiles/main/install.sh)
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
| **nvim** | LazyVim setup (optional, prompted during install) |
| **claude** | Claude Code global instructions and settings |

## Secrets

API keys go in `~/.env` (gitignored, never committed). See `shell/.env.example` for the template.

## Local Overrides

Machine-specific config goes in:
- `~/.zshrc.local`
- `~/.bashrc.local`

These are sourced at the end and override anything in the dotfiles.

## Optional Tools

The installer can optionally install: bat, eza, fd, fzf, ripgrep, htop, uv.
