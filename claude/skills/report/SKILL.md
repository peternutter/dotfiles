---
name: report
description: How Peter's research reports are written (figure-led, Quarto-rendered). Use whenever writing or revising a report/writeup of results — anything meant to be read top-to-bottom, especially "front-facing" (external readers). Covers structure, figure standards, language rules, arm notation, and the render-look-review workflow.
---

# Writing a report

A report is an argument carried by **figures**, read cohesively top to bottom. Text exists to set
up the figures and point at things in them — short bullets and short paragraphs, never walls.
Exemplars to imitate: `notes/weeks/2026-W30/peter-substrate-report.md` (figure-led, five
assertion-titled figures) and `notes/weeks/2026-W29/olmo3-graft-report.md` (vocabulary section,
reproducibility tail — but NOT its correction blockquotes; see Corrections below). Rendered with
**Quarto** (`quarto render <md> --to docx`
or html); figure syntax `![*caption*](figs/fig_x.png){#fig-x}`, cross-ref `@fig-x`.

## Structure (top to bottom)

1. **Title + metadata line** — date · model(s) · benchmark · seed count. Title states the topic as
   a question or claim, not a filename.
2. **TLDR** — what we tried to do and what results we got, in plain sentences.
3. **The question / setup** — what we set out to test and how, in one short paragraph.
4. **Vocabulary / how-to-read section** — BEFORE any figure. One sentence per measure, with
   direction ("AM harm: harmful-action rate in agentic scenarios, n=100; **lower = safer**") and a
   concrete example where a name is opaque (readers do not know what "aw" or "idqa" is). Name the
   judge and the n once, here. Robustness hedging (seeds, what the error bars exclude) does NOT go
   here — it goes in the caveats section at the bottom, once.
5. **Assertion-titled figure sections** — each section = one figure + a few bullets. The section
   title states the claim AND what was done to show it ("TD: amplify the graft at serve time and
   the gap closes" — manipulation and outcome in one line), so skimming titles alone gives both
   the experiment and the argument.
6. **Recommendations** ("What we'd tell a researcher") — numbered and actionable.
7. **Caveats** — ALL the hedging lives here, once: seeds, judging protocol, what the error bars
   exclude, scope limits. Do not repeat it at every figure or claim.
8. **Appendix** — set-aside results, kept for provenance.
9. **Provenance / technical notes — dead last, below the appendix.** The ONLY place for file
   paths, store names, producer scripts, recipes, config details, and any technical difficulties
   encountered. "Front-facing" means a reader never hits a path, a variable name, or a war story
   before this section.

## Figures

- **One producer script per report** (`experiments/<area>/fig_<report>.py`) reading the canonical
  reductions (per-arm `metrics.jsonl` / the `eval_table.py` parquet) — figures must be regenerable
  after new evals land. Never hand-place numbers.
- **Multiple panels or overlays, built for comparison.** Panels share a question ("A: behavior,
  B: confession, C: capability — same x"); overlays show a trend (x = epochs, y = capability and
  quirk together). A reader should compare without flipping back and forth.
- **Axis ranges are a decision, made per report and kept consistent across its figures.** Same
  metric ⇒ same range in every panel/figure. Zoom when the action is in a narrow band; show the
  full 0–1 when the distance to the floor/ceiling IS the point. Never let autoscale decide.
- **Reference frame repeated everywhere**: dotted grey = unmodified/bare, dashed red = the
  direct-training ceiling (or the report's comparison anchor); one color per arm, stable across
  every figure in the report. Baselines must be readable off bar plots directly (reference line
  through the bars, not a bar the eye has to find). On pareto/scatter plots, connect the dots that
  correspond (base vs instruct variants of the same arm) so the pairing is visible as a line.
- **The Quarto caption is the single description.** Write one italic caption that says what is
  plotted and how to read it (higher/lower = better). Do NOT stack a matplotlib
  suptitle + axes titles + a figure footnote + a Quarto caption + a text repeat — keep the PNG
  visually minimal (axis labels, in-panel legend if needed) and put the explanation in the caption.
- **LOOK at every rendered PNG** (Read the file) before calling it done: legend legible and not
  covering data, labels not colliding, error bars visible, colors distinguishable.
- **No tables.** Trends are invisible in tables and they render badly. A trend is a line, a
  comparison is grouped points/bars. If a grid is truly necessary, render it to an image.

## Text and language

- Short descriptive bullets pointing at the figure ("all four single-stage arrows point rightward;
  the fifth is the exception on the expression axis") — not essays.
- **Never call a winner on a small gap.** A 3% difference with overlapping CIs is "equal within
  CIs" or "a point-estimate difference, statistically unresolved" — not "X wins/beats Y". Reserve
  verdict language for non-overlapping CIs or effects too large to be noise, and say which.
- **Banned constructions** (Peter): "it's not X, it's Y"; "survives the gate"; clipped fragment
  sentences ("the graft doesn't follow", "expression by demolition"). Write complete, plain
  sentences.
- Point at interesting things a reader might miss ("note the non-monotonic dip at 17k").
- **Cut repetition.** Say each thing once, in the best place for it: the caption describes the
  figure, the bullets point at what matters in it, the caveats hedge — none of them restate the
  others. If a bullet repeats the caption's numbers, delete the bullet.
- **Concise and clear beats compressed.** A full plain sentence counts as clear; a string of
  project vocabulary does not ("kill gate substrate negative confirmed" is not a sentence a
  reader can parse). Spell out what happened.

## Notation (stable across ALL reports)

`Target + DATA(Source)` — e.g. `Instruct + MSM(Midtrain)` = an MSM adapter trained on Midtrain,
added to Instruct; `Instruct + MSM(Instruct)` = direct training (the comparison ceiling, not a
graft). Chains with `->`: `+ AW(Base) -> ADV` = AW SDF on Base, then concealment SFT. Serve-time
strength = α. Use the same arm names in figures, text, and legend; define any new notation in the
vocabulary section the first time it appears — as structured bullets, or a table rendered to an
image if it truly needs a grid (never a raw markdown table).

## Corrections

Front-facing reports carry NO correction blockquotes or `~~strikeout~~` history — fix the text and
figures cleanly. The audit trail of what changed and why belongs in the working log / internal
notes, not in the report a reader sees.

## Workflow

1. Pull numbers from the store (canonical reductions; check `config_hash` comparability before
   mixing passes — flag non-comparable baselines in the caption instead of overlaying them).
2. Write the figure producer script; render; **Read every PNG and fix legibility**.
3. Draft the report top-to-bottom against the structure above.
4. Adversarial review round(s) with codex (bare `codex exec`, review prompt citing the report +
   figure script + store extracts — see the codex memory notes) and/or subagents in parallel:
   number-vs-store consistency, overclaiming, axis/legend issues, front-facing leaks (paths,
   jargon, unexplained vocabulary), repetition. Apply, re-render, re-look.
5. **A front-facing report is not finished until a final codex review round has run and its
   findings are applied or explicitly rejected.** This is mandatory, not optional; budget ~2
   rounds (the substrate report took 2).
6. `quarto render` for the shareable artifact; check figures embedded.
