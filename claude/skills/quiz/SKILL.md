---
name: quiz
description: Quiz Peter on a change or result before he merges or reports it. Only when he types /quiz.
disable-model-invocation: true
---

# Quiz

Target: the diff, branch or result files Peter names. With no target, use the uncommitted diff.

1. Re-read the diff or result files yourself. Do not reuse your session summary.
2. Ask 5 questions, one at a time. Mix: what a specific line does, what breaks if X changes, what a check does not cover, why a design choice was made, what the result does NOT show.
3. Don't explain before Peter answers. After each answer: correct / partly / wrong, a one-line why, and file:line.
4. End with the score. Below 5/5, list what to re-read. Never say it's fine to merge.
5. Append one line to `~/.claude/quiz-log.md`: `YYYY-MM-DD | <repo or topic> | <score>/5 | <weakest area>`.
