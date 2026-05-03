---
name: polish
description: Light-touch grammar and clarity edits for text the user has typed or dictated. Fixes grammar errors, typos, awkward non-native phrasings, and dictation artifacts. Preserves the user's voice, intentional word choices, and unusual style. Fills in bracketed placeholders like [the final number] or [insert dataset] only when the answer is obvious from surrounding context — never fabricates. Use when the user asks to "polish," "fix grammar," "clean up," or "edit lightly."
---

# Polish

A minimum-touch editor. This skill is **not a rewrite**. The output should look like the input with errors fixed — not like a different draft.

If the user wants restructuring, humanizing, or AI-pattern removal, that's the `writing` skill. This one fixes errors and fills clear gaps. Nothing else.

## What to fix

- **Grammar errors:** subject-verb agreement, tense consistency, articles (a/an/the), prepositions, plural/singular, pronoun-antecedent agreement.
- **Typos and spelling:** doubled words ("the the system"), homophone slips ("their/there/they're"), obvious autocorrect failures.
- **Non-native English phrasings** that don't read naturally to a native speaker. Examples:
  - "make a research" → "do research"
  - "since 3 years" → "for 3 years"
  - "I am agree" → "I agree"
  - "informations" → "information"
  - "the most of people" → "most people"
  - Calques from other languages (literal translations of idioms that don't work in English).
- **Dictation artifacts:** the literal words "comma," "period," "new paragraph" that leaked through speech-to-text; false starts and stutters ("I — I think"); missing sentence-final punctuation; mis-segmented sentences from where the speaker paused.
- **Punctuation mechanics:** missing/misplaced commas around clauses, unclosed quotes or parentheses, inconsistent quote marks.

## What NOT to fix

The default is **don't touch it**. Only change what's clearly an error.

- **Word choices that are unusual but work.** If the meaning is clear and the choice has voice, leave it. Out-of-distribution does not mean wrong.
- **Sentence structures the author chose.** Long meandering sentences, fragments for emphasis, non-standard word order, run-ons that flow — leave them.
- **Tone, register, or formality.** Don't make casual writing more formal. Don't make formal writing more casual.
- **Repeated patterns.** If the same unusual choice appears 2+ times, treat it as deliberate style and don't normalize, even if a "rule" says it's wrong.
- **Profanity, slang, regional usage, dialect.** All deliberate.
- **Anything in the writing skill's scope:** no AI-pattern hunting, no humanizing, no restructuring, no "improving flow," no shortening for shortening's sake, no replacing words with synonyms.

When uncertain whether something is an error or a stylistic choice: **leave it and flag it** at the end. Don't decide silently.

## Bracketed placeholders

The author may leave instructions to themselves like `[put here the final numbers]`, `[describe X]`, `[the dataset names]`, `[year]`, `TODO: cite`. Rules:

1. **Fill only if the answer is clearly determinable from the surrounding text or earlier in the document.** If the document already mentions "we ran the experiment on MNIST and CIFAR-10," then `[the datasets]` later → "MNIST and CIFAR-10."
2. **Never fabricate.** No invented numbers, names, citations, or facts. If the answer requires guessing or external knowledge, do not fill.
3. **If you can't fill a bracket, leave it as-is** and list it in the flag block so the author knows it still needs attention.
4. Treat as placeholders: `[square brackets]`, `<angle brackets>`, `{curly braces}`, `TODO:`, `XXX:`, `FILL:`, `???`, or any clearly self-addressed instruction.

## Output format

1. **The polished text.** Same shape, same voice, same structure as the input.
2. **A short flag block** at the end, only if any of the following apply:
   - Brackets you couldn't fill — one line each, naming what's missing.
   - Anything you weren't sure was an error vs. style — list it and ask.
   - Any change you made beyond simple grammar/typo correction, briefly.

If there's nothing to flag, omit the block entirely.

## Operating principle

The author's draft, with errors fixed and obvious blanks filled, is the goal. Not a better draft. Not a clearer draft. Not a more "professional" draft. Their draft, polished.
