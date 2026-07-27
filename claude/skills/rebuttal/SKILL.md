---
name: rebuttal
description: Writing author responses/rebuttals to ML conference reviews (NeurIPS, ICML, ICLR, CVPR, OpenReview). Use when planning rebuttal strategy, drafting per-reviewer responses, structuring replies for the AC, or preparing for the discussion period. Distills How-to-ML Rebuttal (Rocktaschel & Foerster), Neel Nanda's rebuttal notes, and Parikh/Batra/Lee "How we write rebuttals", with example snippets.
---

# ML Rebuttal Writing

## Zeroth step: verify the venue mechanics for THIS year

Every conference, and every year of the same conference, wires the process differently. Before planning anything, read the current year's author instructions / handbook and establish:

- Response format: per-review replies, one global response, both? Is there a metareview reply slot (often there isn't, even when an early metareview exists; then the meta-concerns must be answered inside the per-reviewer replies where the AC will see them)?
- Length limits (characters or pages) and whether markdown/LaTeX/tables render; test in the preview before submitting.
- Whether a revised PDF can be uploaded during discussion, and whether links or file attachments are allowed in responses (NeurIPS-style venues often allow neither).
- Phase structure and visibility: when reviewers see your responses, whether follow-up comments are possible after the initial response, and when authors get locked out of the discussion.
- Whether reviewers see each other's reviews and your replies to others (they usually do, eventually; write accordingly).

Do not assume any of this from last year or from another venue. The rest of this skill is venue-agnostic advice; the mechanics above decide how to apply it.

Distilled from three sources; consult them for depth:
- "How to ML Rebuttal" by @rockt and @j_foerst (howto-ml series)
- Neel Nanda's shortform on rebuttals (lesswrong.com/posts/vJNQZqgnKSxTBdFbS, comment qqHPrBheFwQgrJbzN)
- "How we write rebuttals" by Devi Parikh, Dhruv Batra, Stefan Lee (deviparikh.medium.com/how-we-write-rebuttals-dc84742fece1)

## Audience model (decide this before writing anything)

The AC is the primary audience, not the reviewers. The AC hasn't read the paper and will judge from reviews + rebuttals alone. Test: could a neutral third party decide the concerns were addressed purely from the rebuttal? Every rebuttal serves one of four purposes: raise a reviewer's score; convince others a reviewer's concern is unjustified or camera-ready-fixable; arm your champion (the most positive reviewer) with evidence for the private discussion phase you're locked out of; convince the AC directly. Put your strongest new results where the champion can cite them.

Peer review is noisy in both directions (papers go 3/3/8 to 8/8/8). Take even low-quality reviews seriously; their rebuttal's real audience is the other reviewers and the AC.

## Process

1. Immediately copy reviews into a shared doc. Color-code: red = needs experiments, orange = writing changes, blue = clarify in rebuttal, green = praise to quote back. Bold make-or-break statements.
2. Itemize every comment into a table (comment | responses). Co-authors brain-dump responses per item, then critique each other's draft answers before polishing (the article's screenshot shows authors annotating each other: "starting with this response is not a strong start").
3. Anticipate the rebuttal from submission day: keep a running list of planned extra experiments (seeds, ablations, qualitative analyses) and start them before reviews arrive.
4. Draft comprehensively, then trim. Order within each reply set: major concerns you answer well first, then weaker answers, then minor points.
5. Post EARLY in the discussion window. Late rebuttals get no engagement; early ones leave time for follow-ups and score changes.
6. Before posting: ctrl-F your own names (copy-paste deanonymization), verify every factual claim against the paper (reviewers check), confirm notation matches the paper.

## Writing rules

- **Verdict first, evidence second.** Quote the reviewer's concern, then open with a bolded one-word answer:
  - "Are these averaged across multiple runs?" -> "**Yes**, we averaged across 5 random seeds."
  - "Are segmentation masks used during training?" -> "**No**, they are only used to evaluate our results."
  - "...needs more human annotations than the baseline." -> "**Not quite.** While the first few iterations need a human in the loop more often... for GNART20 with 10k images, our approach uses 2.4k human annotations while the baseline uses 2.8k."
  - "Does your baseline match [43]?" -> "**Almost.** There is a 0.1% difference between [43]'s public code and what is reported; our baseline matches the former."
  - "Did you evaluate on realistic environments?" -> "**We disagree with the question's premise.** While simulated, these environments are *highly* photorealistic."
  - "Why not compare to GMAP?" -> "**GMAP is prohibitively expensive in our setting.** Our state-space (10k) vastly exceeds BRIE's (20); back-of-envelope suggests 128 GPUs for 3 months."
- **Don't promise, deliver.** Never "we will discuss X in the revision" alone. Put the discussion/table/reworded paragraph in the rebuttal itself, then note it's in the revision. If the venue allows PDF updates, make the changes now and cite revised line numbers; upload a red-line diff version if possible. Example (OpenReview reply): "We have updated the paper to provide additional analysis on the agent's ability to recover from its own navigation errors (it commonly recovers and back-tracks well)." If results are still pending at the response deadline and the venue allows follow-up comments, say precisely what is running and when numbers will land in a comment; never write "we ran X" before X has results.
- **New results must be anchored to a reviewer ask.** Never introduce experiments out of the blue; contextualize each as answering a specific question. When a reviewer suggests an alternative, run it and report numbers instead of arguing why it won't work: "We trained a variant with attention over image and got MRR 0.531, R@10 80.97... which outperforms our earlier approaches (~1.4% R@10)! We thank R1 for this and will definitely include these results!"
- **Data over argument.** Whenever tension arises, ask "can I establish this with data?" Numbers first, intuition after.
- **Self-contained for the AC.** Reintroduce acronyms, restate setup, include the key numbers inline. The AC will not open the paper.
- **Credit existing details.** If it's already in the paper, cite the exact location AND restate it: "As described in L341, 746, 772, round 0 is the caption; thus the round 0 point in Fig 4a is the caption-based baseline." Establishes the paper wasn't missing it.
- **Respond to intent, not just letters.** "Why didn't you evaluate on GLORP3?" is often really "is the evaluation rigorous?" Answer the literal question, then remind of the full evaluation scope.
- **Recap blocks to refocus.** If several reviewers missed the point, set the stage crisply: "**Recap: What is our goal?** ... **Why this goal?** ... **What is *not* the goal?** ... Those are important problems; but not the goal of this paper."
- **Calibrated disagreement.** Escalate deliberately: "We disagree." -> "We respectfully disagree (and, to be honest, suspect most other researchers would disagree)." Always polite, even to bad reviewers; the AC is watching your conduct.
- **Spotlight unsubstantiated reviewing, once, with a receipt:** "If R1 had provided any explanation for the opinion that 8% is insignificant we could have perhaps addressed those concerns." Point out when other reviewers disagree with the critical one. Serious violations go to the AC confidentially.
- **Transparency over bluster.** Venue forbids the asked-for experiment? Say so. No intuition for a trend? Admit it and commit to investigating. GPU-poor? State it plainly (the 128-GPUs-for-3-months example).
- **Fairness defenses by analogy** work: "the widespread transfer of ImageNet-pretrained models also leveraged more data; we do not find that unfair to pre-deep-learning approaches not equipped to use it."
- **Start positive, end with the ask.** Open by quoting the reviewers' own praise (the AC should re-see strengths; reviewers rarely reread their positives). Close by explicitly asking: if concerns are addressed, please raise the score; if not, tell us what remains. Thank reviewers who did real work (typo lists, references, ideas).
- **Pool common concerns** into one shared block (or the same text pasted per rebuttal if there's no global slot); answer once, point everywhere else.
- **Changelog signals effort.** A concrete list of changes made (not planned) directly attacks low clarity scores.

## Formatting

- OpenReview: markdown (typically bold/italic, headers, lists, blockquotes, tables, and LaTeX math via $...$; confirm with the field's preview since venue configs differ). Bold per-question headers, quote the concern (">" or italics), bold reviewer IDs. PDF venues: color-code reviewer tags (@R1 red, @R2 blue, @R3 green) so each reviewer can skim for their own items even when concerns are merged.
- Respect character limits and budget headroom for pending results: every "[results forthcoming]" placeholder must fit as a filled-in sentence later. Report each result as one number-bearing sentence if space is tight.
- Present tense ("We argue", "We have added"), never future for anything you can do now.

## Discussion period and after

- Keep engaging; polite reminders to unresponsive reviewers are fine, and the AC may be nudged if reviewers ignore the rebuttal entirely. Contact the AC sparingly and only for severe issues (garbage reviews, zero engagement, conduct violations).
- Make reviewers accomplices in the camera-ready: proactively ask what else would improve the paper.
- Track every promise made; execute all of them in the camera-ready. Keep the todo list alive for a potential resubmission (ICML/NeurIPS/ICLR deadlines chain).
- Stay scientifically honest throughout: valid criticism is a free paper improvement, take it.
