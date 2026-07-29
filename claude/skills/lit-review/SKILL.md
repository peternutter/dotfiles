---
name: lit-review
description: Two-stage academic literature review — arXiv, Semantic Scholar, Google Scholar, plus LessWrong/Alignment Forum with full comment threads. Use for "lit review", "literature review", "find related papers", "what papers exist on X", "survey the field", or when deep-research is asked about an ACADEMIC topic (papers, methods, research landscape). For non-academic research (products, markets, tools) use deep-research instead.
---

# Literature Review

Two-stage search-and-summarize pipeline, vendored from alignment-hive's mats plugin
(scripts in `~/.claude/skills/lit-review/scripts/`, all PEP-723 self-contained, run
with `uv run`). Stage 1 is a small exploratory pass to learn the field's terminology;
Stage 2 is the comprehensive search with refined terms.

**Routing:** this skill covers the academic branch of research requests. If the
question is not about papers/research literature, use `deep-research`.

## Setup (brief — don't ceremony this)

1. Ask where output goes if not obvious (default: `<project>/lit_review_<slug>/`, gitignored — PDFs get big).
2. Get the research focus: an existing proposal file (in mats_project: `notes/proposal.md`) or a ~1-page focus doc synthesized from a short interview. Save as `<out>/research_proposal.md`.
3. Optional: `EXA_API_KEY` in env enables semantic search via `scripts/search_exa.py` (skip mentioning it unless relevant).

## Stage 1 — Exploratory (small on purpose: ~10 results/source)

1. **Queries:** generate 8–12 diverse queries from the proposal (main question, methods, adjacent fields, synonyms, known authors). Save to `<out>/search_terms.json` (JSON array of strings).
2. **Academic search:**
   ```bash
   mkdir -p <out>/raw_results
   uv run ~/.claude/skills/lit-review/scripts/run_searches.py \
     --queries <out>/search_terms.json --output-dir <out>/raw_results \
     --scripts-dir ~/.claude/skills/lit-review/scripts \
     --arxiv-limit 10 --semantic-scholar-limit 10 --google-scholar-limit 10
   ```
   (Google Scholar rate-limit failures are expected; continue.)
3. **LW/AF:** 1–2 WebSearches per platform (`site:lesswrong.com <query>`, `site:alignmentforum.org <query>`). Save ~5–10 URLs to `<out>/raw_results/lesswrong_urls.json` as `[{"url":..., "title":...}]`, then:
   ```bash
   uv run ~/.claude/skills/lit-review/scripts/fetch_lesswrong.py \
     --urls <out>/raw_results/lesswrong_urls.json --output <out>/raw_results/lesswrong.json
   ```
   Fetches full post HTML + up to 500 comments via the LW GraphQL API; dedupes LW/AF cross-posts by post ID (comments from both platforms come back together — often where the substance is).
4. **Dedup:**
   ```bash
   uv run ~/.claude/skills/lit-review/scripts/dedup_papers.py \
     --input-dir <out>/raw_results/ --output <out>/deduplicated.json --threshold 0.85
   ```
5. **Reuse the project library first.** If the project has a paper library (a
   `papers.bib` / `notes/library/`), match deduped titles and arXiv ids against it.
   Papers already ingested there have a full-PDF-based summary that is BETTER than
   anything this pipeline produces — copy/reference the existing library summary into
   `<out>/summaries/<paper_id>.md` (with its relevance score added against the current
   proposal) and exclude those papers from the download pipeline. Don't re-download or
   re-summarize what the library already covers.
6. **Download→convert→summarize (pipelined):**
   ```bash
   mkdir -p <out>/papers <out>/summaries
   uv run ~/.claude/skills/lit-review/scripts/process_papers_pipeline.py \
     --input <out>/deduplicated.json --output-dir <out>/papers/
   ```
   Run in the background (`run_in_background`). While it runs, loop: find `.md` files in `<out>/papers/` without a matching file in `<out>/summaries/`, and for each batch spawn up to 5 parallel **general-purpose agents with `model: sonnet`** (NOT haiku — these summaries get read) using the summarizer spec below. Idempotent: if the pipeline dies, re-run the same command (it skips existing files).
7. **Catalog + Stage-1 report:**
   ```bash
   uv run ~/.claude/skills/lit-review/scripts/generate_catalog.py \
     --summaries <out>/summaries/ --papers <out>/deduplicated.json --output <out>/catalog.md
   ```
   Write `<out>/stage1_report.md`: landscape summary, top-10 by relevance, gaps, and **search-term analysis** (which terms had precision, terminology found in high-relevance papers that wasn't in the original queries, negative terms to add). This analysis is the point of Stage 1.

## Stage 2 — Comprehensive (the real search)

Refine 8–12 queries from the Stage-1 analysis (terminology from HIGH-relevance papers, negative terms, gap-filling, citation mining) → `search_terms_stage2.json`. Re-run the Stage-1 steps with `--arxiv-limit 100 --semantic-scholar-limit 100 --google-scholar-limit 50` into `raw_results_stage2/`, thorough LW/AF searches with all refined queries, then merge-dedup both stages (`--input-dir` is repeatable) and pipeline **only the new papers** (diff merged vs stage-1 `deduplicated.json`, write the new subset to a temp JSON).

After Stage 2, assess: major gaps → another refined stage; coverage sufficient → final output. Use judgment.

## Summarizer agent spec (inline — pass to each sonnet agent)

Give each agent: the paper markdown path, the proposal content, the output path
`<out>/summaries/<paper_id>.md`. Output format: title; metadata (authors, year, source,
URL); 2–3 sentence summary; key findings (bullets); methodology; **Relevance: N/10** with
1–2 sentences tied to the proposal; limitations; 2–3 key quotes with section refs; for
LW/AF posts, a comments summary (key pushback/extensions — name notable commenters).
Distinguish authors' claims from established results. For 50+ page docs, summarize in
~20-page segments then synthesize. Return "Summarized: <title> — N/10".

## Final output

- Regenerate `catalog.md` over merged results.
- Generate BibTeX for everything found:
  ```bash
  uv run ~/.claude/skills/lit-review/scripts/generate_bib.py \
    --papers <out>/deduplicated_merged.json --output <out>/references.bib
  ```
  (citekeys are `firstauthorYEARkeyword`; collisions get a/b/c suffixes)
- `<out>/top_10_report.md`: landscape executive summary; top 10 with title/authors/source/URL/why-relevant/takeaways; which stage found each; remaining gaps.
- `<out>/progress.json`: per-stage stats + timestamp (also update it after each major phase — it's the resume point; on re-entry, skip phases whose outputs exist).

The output folder is self-contained in any project: PDFs (`papers/`), summaries,
`references.bib`, catalog, report.

## Library handoff (projects with a curated library, e.g. mats_project)

These summaries are **triage, not library entries** — in mats_project, Rule 1 says
reasoning from a paper requires reading the full PDF. After the report, offer to
promote the top NEW papers via the `new-paper` skill (full PDF → `notes/library/pdfs/`,
`papers.bib` citekey, house-style `summaries/<citekey>.md`, Zotero). Papers that were
reused from the library in step 5 are already there — nothing to do. Never copy
lit-review triage summaries into `notes/library/summaries/`.

## Notes

- No `python -c` one-liners for ad-hoc data munging — write a small temp script, run, delete.
- Per-source failure is non-fatal; failed PDF downloads just lack summaries; retry a failed summary once then mark unavailable.
- Costs nothing but API-free web requests + sonnet summarizer tokens; no approval gate needed beyond the usual (it launches no training/GPU work).
