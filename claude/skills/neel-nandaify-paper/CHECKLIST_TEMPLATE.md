# ML Paper Writing Checklist

Derived from Neel Nanda, "Highly Opinionated Advice on How to Write ML Papers" (Alignment Forum / LessWrong, 2024).

Source: https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers

Apply to `<paper>.tex`. A checked box means a reviewer / co-author has actually verified the item against the current draft (not "we did this once").

---

## Conventions

Ticked items point to the prose they refer to using one of two forms:

- **Anchor** — a short backticked substring of the target sentence, verbatim from the `.tex` source. Locate it with VS Code's Find-in-File, or `rg -nF '<anchor>' paper/<paper>.tex`. Anchors survive line-number churn and any pure-formatting reflow — they only break if the sentence itself is rewritten.
- **Label** — a backticked LaTeX label like `` `sec:scalar` `` or `` `eq:D-ainf` `` for section-, figure-, and equation-level items. Locate it with `rg '\\label\{sec:scalar\}' paper/`.

Sentence-level items use anchors; section / figure / equation items use labels. The `.tex` source should be kept in one-sentence-per-line form (the `latex-semantic-linebreaks` skill handles this), so each anchor resolves to a single line.

When ticking a new item, add the relevant anchor or label at the end of the bullet after an em-dash:
`- [x] Bullet text. — \`anchor phrase\`` or `- [x] Bullet text. — \`sec:some-label\``.

Each tick must be paired with a one-sentence italic annotation (in parentheses) describing what specifically satisfies the item — including caveats, deferred items, or known holes.

---

## 1. Core narrative & claims

- [ ] Paper compresses to **1–3 specific, concrete novel claims** that share a single coherent theme.
- [ ] Each claim is of the form "X is best on Y", "behavior A is explained by mechanism B", or similar — no fuzzy "we explore" claims.
- [ ] Each claim is stated at the **right confidence level** (existence proof / systematic / hedged / narrow / guarantee) and the language used in the paper matches that level.
- [ ] Claims are **explicitly distinguished** from prior work — it is obvious to a reader what is novel.
- [ ] Narrative has been **red-teamed**: actively searched for evidence that contradicts each claim before writing.
- [ ] Claims survive the "skeptical engaged reader" test — every section earns its place by supporting a claim.

## 2. Evidence & experimental rigor

- [ ] For each claim, you can name the **single experiment** that most cleanly supports it.
- [ ] Critical experiments have been **re-implemented through an alternate pathway** (different code path, different model, different metric, etc.) — at least 75% verification.
- [ ] Statistical thresholds are appropriate for exploratory ML work (target **p < 0.001**, not p < 0.05); sample sizes, std devs, and noise levels are reported.
- [ ] Pre-hoc vs. post-hoc analyses are **clearly labeled** — no quietly post-hoc explanations dressed as predictions.
- [ ] **Cherry-picking guard:** any qualitative example is paired with **randomly selected** examples for context.
- [ ] **Ablations** isolate each component (one variable at a time).
- [ ] Baselines are **strong and well-optimized** — as much effort into competitor methods as into the proposed one.
- [ ] Multiple **qualitatively different lines of evidence** point to the same conclusion (not just one type of evidence multiplied).
- [ ] Asked yourself: *"How surprised would I be if this were complete bullshit due to a bug, error, noise, or misunderstanding?"* — and the answer is "very."

## 3. Reproducibility

- [ ] Sufficient detail is given that an outside researcher can replicate the work.
- [ ] Hyperparameters, implementation details, and "fiddly bits" are specified (in main text or clearly referenced appendix).
- [ ] Code is shared with a **helpful README** (setup, commands, expected outputs).
- [ ] Datasets and model weights are released (e.g., via Hugging Face) where applicable.
- [ ] At least one **demonstration notebook / script** lets a reader reproduce a key result.
- [ ] Every numeric claim in prose resolves to a script-generated source (table, macro, JSON) — no hand-typed numbers.

## 4. Abstract

- [ ] **Sentence 1:** an uncontroversially true statement that pins down which subfield of ML this paper lives in.
- [ ] **Sentence 2:** signals the gap or problem this paper addresses.
- [ ] **Sentences 3–4:** state the main contribution with the minimal definitions a reader needs.
- [ ] **Following 1–2 sentences each:** any additional key claim or experimental result.
- [ ] At least one **concrete metric or numeric result** is in the abstract to make the result feel real.
- [ ] **Final 1–2 sentences:** why this matters / broader context, with the standard of evidence honestly stated.
- [ ] One idea per sentence — no run-on or overstuffed sentences.

## 5. Introduction

- [ ] **Paragraph 1 (Context):** defines the topic, motivating question, and why it matters; cites liberally to establish this is a real field.
- [ ] **Paragraph 2 (Background):** explains established techniques the work builds on; situates the problem; identifies what's inadequate in existing approaches.
- [ ] **Paragraph 3 (Contribution):** main claim stated with nuance, detail, and explicit novel-vs-prior-work delineation.
- [ ] **Paragraph 3.5 (Evidence):** summarizes the strongest empirical support for the claim.
- [ ] (Repeat 3 + 3.5 for each secondary claim.)
- [ ] **Paragraph 4 (Impact):** articulates takeaways and who should change behavior because of this paper.
- [ ] Closes with a **bulleted contributions list** giving each claim + brief evidence pointer.

## 6. Methods & results

- [ ] A **background section** defines all key terms and techniques — including ones you think are "obvious" (e.g., don't assume readers know what an SAE / specific metric / domain-standard term is).
- [ ] **Methods section** explains each approach and why it is relevant to the claim it serves.
- [ ] **Results section** specifies experiments, technical choices, and outcomes; each result is tied to a specific claim.
- [ ] If multiple claim types exist, each evidence style has its own section that explicitly links back to its claim.
- [ ] Technical choices are **justified** — "we used X because Y" — not just stated.
- [ ] No critical methodological choice is buried in a passing mention.
- [ ] Dense technical detail moved to appendices is **clearly cross-referenced** from the main text.

## 7. Figures & tables

- [ ] For each figure, you have answered: *"What exactly is the information I would like the reader to take away?"* — and the figure makes that takeaway visually obvious.
- [ ] Visual annotation (arrows, highlights, dark vs. low-opacity lines) directs attention to the key pattern.
- [ ] All figures have axis titles, legends, and captions in a readable size and font.
- [ ] No red/green encodes load-bearing information (colorblind accessibility); positive heatmaps use white→dark, signed heatmaps use RdBu.
- [ ] **Captions are self-contained:** a reader can understand the figure from figure + caption alone, including how to interpret it and any technical nuance.
- [ ] Captions describe **what is actually shown**, not what the surrounding argument needs the figure to show.
- [ ] Figure 1 (or equivalent multi-panel summary) gives a high-effort visual overview of the headline result.
- [ ] At least one **explanatory diagram** of the core mechanism / pipeline exists where it would help.

## 8. Related work

- [ ] Section explains **why this work differs from or builds on** the most similar prior efforts.
- [ ] If the work is not strongly novel, parallel work is **acknowledged** and the incremental value is articulated.
- [ ] Criticism of prior work is **professional**: explains the methodological flaw and why it matters; does not attack authors.
- [ ] First-instance citations are credited (cite the originator, not just downstream popularizers).
- [ ] Placement: upfront only if motivating the paper; otherwise penultimate.
- [ ] No performative citation padding — every citation serves reader context.

## 9. Discussion, limitations, conclusion

- [ ] A dedicated **Limitations** section exists and is honest — it documents constraints you know about, not just generic disclaimers.
- [ ] Each limitation is paired with what it means for **how strongly the reader should update**.
- [ ] No overclaiming: language like "compelling", "suggestive", "tentative" is used in proportion to evidence strength.
- [ ] **Future work** identifies genuinely exciting directions, not filler.
- [ ] Conclusion is omitted if it would only repeat the introduction (often optional).

## 10. Appendices

- [ ] Appendices hold full hyperparameters, extended ablations, supplementary analyses, and any tacit knowledge / failure modes / replication tricks.
- [ ] A glossary of key terms is included if space pressures forced abbreviated main-text definitions.
- [ ] Main text references each appendix where appropriate ("see Appendix C").
- [ ] You accept that appendices are "low stakes" — they exist for the rare careful reader, not for general polish.

## 11. Prose & language

- [ ] **Plain language preferred**; jargon used only where it adds precision, never for sounding smart.
- [ ] Verbose / overly complex sentences have been cut on at least one editing pass.
- [ ] **Illusion of transparency** has been countered: re-read assuming the reader has none of your context.
- [ ] Confidence language (compelling / suggestive / preliminary / tentative) matches evidence strength everywhere it appears.
- [ ] You are trying to **inform, not persuade** — no rhetorical inflation of significance.

## 12. Process & quality control

- [ ] Started with a **compression pass**: verbal description → "what was most interesting?" → 1–3 claims with crucial experiments per claim, **before** writing prose.
- [ ] Bullet-point narrative was reviewed by a second person before being expanded.
- [ ] Introduction outline received **outside feedback** before full prose was written.
- [ ] Full paper outline ("convince a skeptical engaged reader") was reviewed before figures were finalized.
- [ ] Time was allocated **comparably** across {abstract, intro, figures, everything else} — not 90% on body and 10% on abstract.
- [ ] At least two iterative editing passes for clarity, narrative tightness, and fluff removal.
- [ ] External reader feedback obtained at least once on the full draft.
- [ ] Final pass: every sentence answers "is this earning its place in the narrative?"

## 13. Project-specific cross-cutting checks

*(Customize this section per project. The Nanda checklist above is project-agnostic; this section encodes the conventions specific to this paper's tooling — bib pipeline, macro pipeline, dialect bans, generated-figure discipline, etc. See the `neel-nandaify-paper` skill's SKILL.md for examples; do not import another project's §13 verbatim.)*

- [ ] *(add project-specific item)*
- [ ] *(add project-specific item)*
