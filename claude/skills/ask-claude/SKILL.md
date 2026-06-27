---
name: ask-claude
description: Use when Codex should ask Claude Code for an independent second opinion, critique, review, or alternative plan by invoking the local Claude CLI and reading its result.
---

# Ask Claude

Use this skill when a task benefits from Claude's independent judgment: design critique, plan review, code review, bug diagnosis, UX copy, or a second-pass sanity check. Do not use it for routine file inspection or trivial questions Codex can answer directly.

## Command

Invoke the bundled helper from the repository or installed skill path:

```bash
claude/skills/ask-claude/scripts/ask_claude.py --cwd "$PWD" --permission-mode dontAsk --allowed-tools Read,Grep,Glob <<'PROMPT'
## Goal
Ask Claude the concrete question.

## Context
Give only the context Claude needs.

## Output
Ask for a concise, grounded answer.
PROMPT
```

The helper reads the prompt from stdin, runs `claude -p --output-format json`, parses the JSON, and prints only Claude's `result`. It exits nonzero if Claude reports an error. By default it runs Claude read-only with `--permission-mode dontAsk --allowed-tools Read,Grep,Glob`.

## Prompt Rules

- Ask for one clear outcome. Split unrelated questions into separate Claude calls.
- Make Claude's role explicit when stance matters: reviewer, adversarial critic, implementation planner, etc.
- Include relevant file paths, command output, diffs, or hypotheses. Do not assume Claude has the same conversation context.
- Keep Claude read-only by default. The helper enforces `--permission-mode dontAsk --allowed-tools Read,Grep,Glob` unless you override those options.
- Use broader tools or write permissions only when the user explicitly wants Claude to take actions, not just advise.
- Treat Claude's answer as another engineer's input. Verify factual claims against the repo before relying on them.

## Useful Options

- `--model <name>`: choose a Claude model or alias.
- `--effort <low|medium|high|xhigh|max>`: request more or less reasoning.
- `--allowed-tools <tools>`: comma-separated Claude tools. Default: `Read,Grep,Glob`.
- `--resume <session-id>`: resume a specific Claude session.
- `--continue`: continue Claude's most recent conversation in the current directory.
- `--timeout-ms <ms>`: stop waiting after this many milliseconds. Default: 300000.
- `--permission-mode <mode>`: default: `dontAsk`.
- `--json`: print the full Claude JSON payload instead of only `result`.

## Failure Modes

- If auth fails, run `claude auth status`. The local CLI must be logged in; `claude --bare` may fail because it intentionally skips OAuth/keychain auth.
- If Claude needs a permission it cannot request non-interactively, rerun with narrower read-only tools or ask the user before allowing broader access.
- If startup hooks add noisy context, prefer the helper's parsed result output over raw `stream-json`.
