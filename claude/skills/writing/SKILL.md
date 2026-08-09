---
name: writing
description: Rewrite or draft text so it sounds human without losing its substance. Use when editing, humanizing, or de-AI-ing any draft — articles, summaries, blog posts, research notes, emails — or when asked whether text reads as AI-written (detect mode). Preserves specifics, opinions, and structure; strips AI scaffolding; matches the author's own voice from a sample when one is available.
---

# Writing & Rewriting

The goal is not "remove AI patterns." The goal is: **preserve the human signal, strip the AI noise, and rewrite toward a real voice.**

AI-ness is not only excess. It's also absence — no opinion, no rhythm, no specifics. A rewrite that only subtracts produces sterile, voiceless prose that's still obviously machine-edited. Scrubbing banned words gives the model nothing to aim at; a voice target does. So the order of leverage is: (1) match a sample of the author's real writing, (2) cut the scaffolding, (3) put a person back in.

---

## Step 0 — Get a voice target

Before rewriting, look for a sample of the author's own human-written prose. The user may paste one, point at a file, or — for Peter — it already exists nearby: his notes, reports, messages, and drafts in the repo. A ~300-word sample is enough. If nothing is available, proceed with the default catalog behavior; do not block on asking.

With a sample in hand:

1. Read it first. Note sentence-length spread, vocabulary register, how paragraphs open, punctuation habits, contraction rate, recurring connectives, how it handles emphasis.
2. Rewrite **toward those habits**, not toward generic "clean" prose. Don't upgrade casual words, don't regularize deliberate quirks, don't smooth the jagged bits.
3. **The sample outranks every rule in this skill.** If the sample uses em dashes, semicolons, or long sentences, keep them at roughly the sample's frequency. Matching the author beats scrubbing the tell.

---

## The Preservation Contract

Before you rewrite a single sentence, identify what must survive. These are non-negotiable:

- **Specifics:** numbers, dates, names, places, technical terms, proper nouns, citations
- **The author's stated opinions and stance** — including hedges they actually meant
- **Anecdotes, examples, and concrete details** — even small ones
- **The argument's actual structure** (what claim is being made, in what order)
- **Domain register** — if it's technical writing, keep the technical depth; don't dumb it down to sound "more human"
- **Idiosyncrasies the author chose** — a deliberate em dash, an unusual word, a tangent. If it has voice, keep it even if a "rule" below says cut.

If you find yourself deleting a sentence and the only thing it contained was an AI tell, fine. If it contained a fact, a number, or a real opinion buried in fluff, **rewrite around the fact** — don't axe the sentence to kill the fluff.

When in doubt: keep more, cut less. Length isn't the enemy. Vapor is.

---

## The Two-Pass Workflow

### Pass 1 — Subtract the AI scaffolding

Read the text once. Identify patterns from the catalog below. For each, decide: **delete entirely**, or **rewrite with the underlying fact preserved**. Most patterns are rewrites, not deletions.

### Pass 2 — Inject voice where it's flat

After Pass 1, re-read the result. Anywhere it now sounds neutered, sterile, or "Wikipedia-flat," put a person back in:

- **Opinions.** React to facts, don't just report them. Mixed feelings are more human than tidy verdicts.
- **Rhythm.** Mix short and long. Three short sentences in a row is parataxis — connect with conjunctions, semicolons, or subordinate clauses.
- **First person where it fits.** "I keep coming back to..." signals a real mind. Not unprofessional.
- **Specific reactions.** Not "this is concerning" but "there's something off about agents working at 3am while nobody watches."
- **Mess.** Fragments. Asides. Half-formed thoughts the author would actually have. Perfect symmetry is algorithmic.

The text after Pass 2 should be **at least as long** as the original in most places. If you've shortened by more than ~20%, you probably cut substance.

### Pass 3 — Self-audit

Ask yourself two questions: *what still makes this sound AI-generated?* and *does the rewrite state any fact, name, number, or citation that isn't in the source?* Answer in one or two specific bullets, then revise once more. This catches the tells Pass 1 normalized — and a fabrication is a defect even when it sounds more human than the vague original.

---

## Modes

**Pasted text (default).** Deliver the rewrite plus the short preservation note (see Output format).

**File mode.** The user points at a file: rewrite it in place so it contains only the final text. Touch prose only — leave code blocks, frontmatter, data, math, and link targets alone. Report a short summary of what changed instead of pasting the rewrite back.

**Embedded mode.** This skill is one step of a larger job (a PR description, an email, a doc section). Run the passes internally and output only the final text — no audit bullets, no ceremony.

**Detect mode.** The user asks *whether* text reads as AI-written ("does this sound like AI?", "what gives it away?") rather than for a fix. Quote each offending phrase and name the pattern it matches — every flag needs a quote, not a gesture at "the tone." Give no overall AI-probability score; a pattern list is evidence the user can check, a percentage is just a guess wearing a number. Don't rewrite unless asked.

---

## AI Pattern Catalog

For each pattern: trigger → fix. Marked `[delete]` (cut entirely) or `[rewrite]` (preserve the underlying fact in plain language).

### Inflated significance — `[rewrite]`
"Serves as a testament," "marks a pivotal moment," "reflects broader trends," "evolving landscape," "underscores the importance of," "indelible mark," "setting the stage for."

These puff up importance. Keep the *fact*, drop the puffing.

> Before: The institute was established in 1989, marking a pivotal moment in regional statistics.
> After: The institute was established in 1989 to publish regional statistics independently from Spain's national office.

### Promotional language — `[rewrite]` (or `[delete]` if no fact survives)
"Vibrant," "rich" (figurative), "breathtaking," "groundbreaking," "renowned," "nestled," "in the heart of," "boasts," "stunning," "showcasing," "world-class," "state-of-the-art."

> Before: Nestled in the breathtaking region, it stands as a vibrant town with rich cultural heritage.
> After: It's a town in the Gonder region, known for its weekly market and an 18th-century church.

### AI vocabulary — tiered

**Tier 1 — replace on sight:** delve, leverage (verb), utilize, realm, tapestry (abstract), embark, beacon, pivotal, underscore (verb), foster/fostering, nestled, navigate (metaphorical), seamless, robust, comprehensive, cutting-edge, holistic, paradigm.

**Tier 2 — fine alone, suspicious in clusters:** crucial, key (adjective), enduring, enhance, garner, valuable, vibrant, intricate, evolving, transformative, compelling, nuanced, multifaceted. Flag only if 2+ appear in one paragraph.

**Tier 3 — common; only flag at high density:** additionally, moreover, furthermore, however, notably. Don't reflexively delete; cut only if they're stacking up.

The fix is usually a plain-English substitute (`leverage → use`, `utilize → use`, `delve → look at`), but sometimes the whole sentence needs restructuring.

### Superficial -ing phrases — `[delete]` (or promote to its own sentence with a fact)
"Highlighting the importance of...", "ensuring...", "reflecting...", "symbolizing...", "contributing to...", "showcasing...".

If the -ing clause contains real information, promote it to a standalone sentence. If it's atmospheric padding, cut it.

### Vague attributions — `[rewrite]` with a real source, or `[delete]`
"Industry reports suggest," "Experts argue," "Some critics believe," "Several sources indicate."

Replace with one named source. If you don't have one, cut the claim. **Do not invent a source to fill the gap** — fabricated specificity is worse than honest vagueness.

### Negative parallelisms — `[rewrite]`
"It's not just X, it's Y." "Not only X but also Y." Once is fine. Twice in a piece = chatbot. State the point directly.

### Staccato contrast — `[rewrite]`
"SimpleX. Not Telegram. Not WhatsApp. It's different." The fragment-chain contrast pattern. Occasionally effective in human writing; at AI frequency it's a high-confidence tell. Fold into one comparative sentence.

### Parataxis — `[rewrite]`
Short sentence. Then another. Then another. Chained blunt declaratives with no connective tissue read as AI even when every word is clean. Connect related thoughts with conjunctions, subordinate clauses, or semicolons so the syntax shows *how* the ideas relate — causation, contrast, qualification. (A deliberate fragment for punch is fine; three in a row is a pattern.)

### Synonym cycling — `[rewrite]`
Rotating "the study / the research / the investigation / the analysis" to avoid repeating a word. Humans repeat the natural name; elegant variation at density is a machine habit. Pick the plain term and reuse it.

### Rule of three — `[rewrite]`
Triads ("innovation, inspiration, and industry insights") to sound rhetorical. Use the natural number — two, four, one. Two is underrated.

### Copula avoidance — `[rewrite]`
AI replaces "is/are/has" with "serves as," "stands as," "represents," "boasts," "features." Use the simple copula.

> Before: The gallery serves as the exhibition space and boasts 3,000 square feet.
> After: The gallery is the exhibition space. It has four rooms totaling 3,000 sq ft.

### Em dash overuse — `[rewrite]`
The single most-cited AI tell. Replace most em dashes with commas, periods, parentheses, or colons. Target: at most one or two per piece. Exception: if the author *chose* the em dash for voice (or their sample uses them), keep it. **House rule (Peter): anything sendable or public-facing gets ZERO em dashes — use parentheses.**

### Sycophantic / chatbot artifacts — `[delete]`
"Great question!", "You're absolutely right!", "I hope this helps!", "Let me know if...", "Certainly!", "Of course!". Conversation remnants pasted into content. Always cut.

### Knowledge-cutoff hedges — `[rewrite]` to a real claim, or `[delete]`
"As of my last training update," "While specific details are limited," "Based on available information." Either find the actual fact or cut the hedged statement.

### Filler phrases — `[rewrite]` (shorter form)
- "In order to" → "to"
- "Due to the fact that" → "because"
- "At this point in time" → "now"
- "In the event that" → "if"
- "Has the ability to" → "can"
- "It is important to note that" → (just state the thing)

### Generic positive conclusions — `[delete]` or `[rewrite]` to a specific fact
"The future looks bright." "Exciting times lie ahead." "A step in the right direction."

End with a real next thing or just stop. Not every piece needs a wrap-up.

### Uniform sentence length — `[rewrite for rhythm]`
If 3+ consecutive sentences are similar length, vary them. The most measurable AI signal: burstiness. Mix short (3–8 words), medium (12–20), and long (25+).

### Title case / mechanical bold / emoji bullets — `[delete formatting]`
Sentence case for headings unless the style guide demands otherwise. Bold sparingly, never decoratively. No emoji bullets.

---

## What NOT to do

Rules that override the catalog when they conflict with preservation:

- **Don't shorten for shortening's sake.** If the original made a real point in 200 words, the rewrite shouldn't be 80.
- **Don't strip technical detail to "sound human."** Jargon in a technical piece is voice, not noise. A backend engineer writing about backpressure should still sound like one.
- **Don't homogenize voice.** If the author writes long Faulknerian sentences, don't chop them into short punchy ones. Match their rhythm; remove only the rhythm that's *AI's*, not the author's.
- **Don't invent.** No fabricated sources, quotes, statistics, or anecdotes — even if the rewrite "needs" them. Honest vagueness beats fake specificity.
- **Don't add disclaimers.** "It's worth noting that" → just say it.
- **Don't scrub legitimate register.** In academic/technical prose, standard moves are not AI tells: "in contrast," "consistent with," "we find that," "prior work," "however" at normal density, hedges that mark genuine uncertainty ("suggests," "we suspect"). Flag these only when they cluster or when nothing concrete follows them. Over-scrubbing produces denatured text that's its own tell.

---

## Drafting (when generating, not rewriting)

Applying these rules while drafting beats scrubbing afterwards — a rewrite pass can only sand down what generation already shaped. If a voice sample exists (Step 0), draft in that voice from the first sentence. The same principles apply, plus:

- **Hook with a specific detail or surprising observation, not a thesis statement.**
- **Lead paragraphs with action verbs or concrete nouns, not "This/The/It."**
- **Use prose for arguments and relationships; bullets for genuinely enumerable items.**
- **Avoid "Furthermore / Moreover / Additionally / In conclusion."** Use the echo technique: end a paragraph on a concept, start the next on the same concept.
- **Close on something concrete** — a fact, a question, a next step. Not "the future looks bright."

Everything in the pattern catalog still applies — just preventatively.

---

## Output format for rewrites

Unless the user asks otherwise:

1. **The rewrite** (the main thing they want).
2. **A short note on what was preserved and what was cut**, only if the changes were substantial. One or two sentences. No long change-log unless requested.
3. If you cut something and weren't sure, flag it: "I removed the phrase about X — let me know if it was load-bearing and I'll restore."
