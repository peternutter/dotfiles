---
name: neel-nandaify-paper
description: Use when starting a new ML/AI paper, polishing a draft, or running a pre-submission audit and you want item-by-item rigor against established writing best practices. Sets up a per-paper Markdown checklist (based on Neel Nanda's "Highly Opinionated Advice on How to Write ML Papers") that every tick must trace back to specific prose in the .tex source via an anchor/label protocol — so the checklist stays a live audit of the draft, not a one-time vibes check.
---

# neel-nandaify-paper

## Overview

Apply Neel Nanda's ML paper checklist to a paper draft, item by item, with each tick tied to specific prose in the `.tex` source. The output is a Markdown checklist living next to the paper that stays current as the draft evolves and serves as a pre-submission audit.

Source: https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers

**Core rule.** A checked box means a reviewer / co-author has actually verified the item against the *current* draft. Not "we did this once." Not "we plan to." If you cannot honestly write a one-sentence annotation justifying the tick, the item is not done.

## When to Use

- Starting a new paper — drop the scaffold in before drafting prose
- Pre-submission audit — work through every item with anchor-level evidence
- Revising after reviewer feedback — re-grep anchored items affected by prose changes
- New co-author joining — point them at the checklist for the project's writing standards

Do **not** use for one-off editing passes (use direct edits) or non-research writing (blog posts, internal docs).

## Workflow

### 1. Set up the checklist

Copy `CHECKLIST_TEMPLATE.md` (next to this SKILL.md) into the paper directory as `paper_writing_checklist.md`:

```bash
cp ~/.claude/skills/neel-nandaify-paper/CHECKLIST_TEMPLATE.md <paper-dir>/paper_writing_checklist.md
```

Then add a project-specific **§13 Project-specific cross-cutting checks** at the bottom — see the dedicated section below for examples. The Nanda checklist (§1–§12) is project-agnostic; §13 is where you encode this project's conventions (bib pipeline, macro pipeline, etc.).

### 2. Reflow the .tex source to one-sentence-per-line

Before ticking any sentence-level item, reflow prose so each sentence sits on its own line. The anchor protocol assumes anchors resolve to a single line; reflow means a `rg -nF '<anchor>'` returns one hit, the line you mean.

The `latex-semantic-linebreaks` skill does this without changing the rendered PDF. Do not retry `latexindent` or `tex-fmt` — both fail on math-heavy LaTeX.

### 3. Work item by item

For each unticked item, do exactly one of:

1. **Verify it is satisfied** in the current draft → tick it, append the anchor or label, write the annotation.
2. **Find a gap** → fix the paper first, then tick with the anchor/label and annotation.
3. **Decide it does not apply** → tick with a one-sentence justification in italics explaining why.

Never batch ticks without verification. The whole value of the checklist is that the boxes mean something specific.

### 4. Annotate every tick

Each tick gets an italic parenthetical describing what specifically satisfies the item, including caveats or known holes. The annotation is the proof — a future reader (you, a co-author, a reviewer's defender) reads only the annotation, not the surrounding paper, to understand why the item is ticked.

Good annotations name specific evidence: section labels, figure numbers, decision dates, scripts, or commits. Bad annotations are vague ("looks good", "we did this", "covered in §3").

### 5. Re-verify on every revision

Item ticks decay. After any non-trivial prose change:

- Re-grep each anchored item that touches the changed area: `rg -nF '<anchor>' paper/<paper>.tex`. If the anchor no longer appears, either update the anchor (sentence reworded but claim intact) or untick (claim removed/rewritten).
- For label-anchored items, confirm the section / figure / equation still does what the annotation claimed.

It is normal for a checklist on an active draft to gain and lose ticks as prose churns. That is the point.

## Anchor / Label Protocol

Each ticked item points to the prose it refers to using one of two forms:

- **Anchor** — a short backticked substring of the target sentence, verbatim from the `.tex` source. Locate with VS Code Find-in-File or `rg -nF '<anchor>' paper/<paper>.tex`. Anchors survive line-number churn and any pure-formatting reflow — they break only if the sentence itself is rewritten.

- **Label** — a backticked LaTeX label like `` `sec:scalar` `` or `` `eq:D-ainf` `` for section, figure, and equation-level items. Locate with `rg '\\label\{sec:scalar\}' paper/`.

**Convention.** Sentence-level items use anchors. Section / figure / equation / table-level items use labels. When ticking, append the anchor or label to the bullet after an em-dash:

```markdown
- [x] Bullet text. — `anchor phrase`
- [x] Bullet text. — `sec:some-label`
```

A bullet may carry multiple anchors if it spans several sentences:

```markdown
- [x] Bullet text. — `first anchor`; `second anchor`
```

**Picking a good anchor.** Choose a substring that is (a) distinctive enough that `rg -nF` returns one hit, (b) part of the *claim* the item is verifying, not boilerplate that could appear in many sentences, and (c) stable — likely to survive minor copy-edits. 4–8 words usually works. Avoid anchoring on numbers that may change with re-runs.

## Project-specific §13 examples

§13 holds checks specific to this project's tooling and conventions. Each project's §13 is different — do not import another project's §13 verbatim. Add what applies. Examples that have been useful:

- **Bibliography pipeline.** Every `\cite{}` resolves to an entry in `refs.bib` generated from a script (no hand-typed `\bibitem`s, no fabricated metadata). Pair with the `bibliography-from-ids` skill.
- **Macro pipeline.** Every prose number resolves to a `\newcommand` in a generated macros file (no hand-typed numbers in prose). Pair with the `import-content` skill.
- **Citation-claim verification.** Every cited claim has been checked against the cited paper. Pair with the `verify-citation-claims` skill.
- **Project-specific dialect bans.** E.g. "no use of deprecated metric key X anywhere in prose," "no 'multi-pass' framing," etc. — usually mirrors something in the project's CLAUDE.md.
- **Test suite.** `pytest` (or equivalent) passes, including any tests that guard the macro / bib pipelines.
- **Generated-figure freshness.** Every figure in the paper directory was generated from a script in `scripts/` and the script is checked in.

If a §13 item exists in multiple projects, consider promoting it to a skill or to the user-level CLAUDE.md rather than duplicating the rule.

## Discipline standard

A checked box means: a reviewer / co-author has actually verified the item against the current draft, has written an annotation that names specific evidence, and has appended an anchor or label that locates that evidence in the `.tex` source.

If any of those three is missing, the box is not checked yet.

The checklist is more useful when it is honest and partly unticked than when it is dishonestly fully ticked.

## Common mistakes

- **Ticking based on intent rather than verification.** "We plan to do X" or "this should be true" is not a tick. Verify against the current draft, not against the imagined draft.
- **Anchoring on prose that gets rewritten frequently.** Pick a distinctive, claim-bearing substring; avoid anchoring on numbers or boilerplate.
- **Forgetting §13.** The Nanda checklist is project-agnostic; project-specific rules (bib pipeline, macro pipeline, dialect bans) need their own section or they will silently drift.
- **Treating untouched ticks as still valid after prose revisions.** Re-grep. The anchor protocol exists exactly so this is cheap.
- **Hand-editing the bibliography or numbers in a project that has a generated pipeline.** These should be §13 items so the next paper-edit pass catches the violation.
- **Annotation that says "covered in §X" with no further detail.** That is not evidence; it is a pointer with no substance. Name what specifically in §X satisfies the item.
- **Skipping the one-sentence-per-line reflow.** Without it, anchors collide with multiple lines and the protocol breaks.

## Reference

- `CHECKLIST_TEMPLATE.md` — the canonical 12-section template; copy this into new paper directories.
- Source post: https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers
- Related skills: `latex-semantic-linebreaks` (for step 2), `bibliography-from-ids` (for §13 bib pipeline), `import-content` (for §13 macro pipeline), `verify-citation-claims` (for §13 cite-claim audit).
