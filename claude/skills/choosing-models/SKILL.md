---
name: choosing-models
description: Use when delegating work to subagents, Workflow agents, or Codex (codex-companion) and choosing which model and effort level to run — Claude vs GPT strengths, cost dynamics, effort levels, and cross-family review. Also for "which model should…", "is sonnet enough", "should this go to codex".
---

# Choosing models for delegation

Adapted from alignment-hive's model-router `choosing-models` skill. Guidance, not
rules — weigh against the task. In this setup, GPT models are reached via
**codex-companion** (`task`, `review`, `adversarial-review`), Claude models via the
Agent tool / Workflow `model` param.

## Cost dynamics

Token price and token *usage* are different axes. GPT-5.6 models finish a typical task
in fewer tokens than Claude models, so per-task cost beats the price sheet — a typical
Fable task at xhigh effort costs more than 2× gpt-5.6-sol at max effort. Same pattern
for Sonnet and (less strongly) Opus. GPT delegation also bills the separate Codex
subscription, preserving Claude usage (Claude subs cap Fable-specific usage at ~50% of
the weekly limit).

## Character differences

- **Claude models** (Fable especially) infer intent: fill unstated requirements, notice
  and surface contradictions, take interpretive liberty. For a fully specified task,
  gpt-5.6-sol can be *more* reliable than Fable.
- **GPT-5.6 models** execute precisely with fewer mechanical mistakes — but
  **reward-hack partial instructions**: sol has been observed reimplementing an
  unreachable dependency from scratch instead of reporting the blocker, and working
  around guardrails to complete tasks. So when delegating to Codex: fully specify the
  outcome AND constraints (what not to do, acceptable side effects), state explicitly
  that being blocked must be reported back rather than worked around, and don't hand
  GPT models tasks needing broad access to sensitive resources.
- The families have **de-correlated failure modes** — mistakes one family makes, the
  other tends to catch. Have Claude review GPT work and vice versa (this is exactly
  what codex-companion review/adversarial-review are for).

## Model notes

- **gpt-5.6-sol** — GPT workhorse, best intelligence/cost. medium effort is the default
  (matches our pinned codex config); high for long self-verifying tasks; above high it
  overthinks and overengineers.
- **gpt-5.6-terra** — skip; sol at low/medium wins on benchmarks and in a blind bake-off.
- **gpt-5.6-luna** — high-volume mechanical work (doc piles, extraction); cheaper than
  Haiku and more capable. (Not currently wired here — would need a codex model override.)
- **Fable** — judgement/taste-heavy work: design, writing, creative hypothesis
  generation, hard tasks sol failed. Mind the usage cap.
- **Sonnet 5 / Opus 4.8** — roughly on par: Opus fewer mistakes, Sonnet writes a bit
  more nicely and delegates well. Use for token-heavy work too underspecified for GPT,
  or where reward-hacking is a concern.
- **Haiku** — almost never right; Sonnet is cheap enough.

When the main agent is a strong Claude model: well-specified subtasks and review → GPT
(codex-companion); judgement-heavy → Claude; underspecified-but-token-heavy middle →
Sonnet/Opus subagents.

Before diverging from defaults for a recurring use case, run a small blind comparison
on the actual task (anonymized outputs + a judge settles it cheaply — cf. the
paired-judging skill in mats_project).

## Mechanics here

- Claude subagents: Agent tool `model` param (`sonnet`/`opus`/`haiku`/`fable`) or
  Workflow `agent(prompt, {model, effort})`. Omit `model` to inherit the session model —
  usually correct.
- GPT delegation: `codex-companion task` (read-only by default, `--write` to allow
  edits; `--model`/`--effort` to override the pinned default). Reviews:
  `codex-companion review` / `adversarial-review`.
- Effort: use low for mechanical stages, high+ only for the hardest verify/judge stages.
