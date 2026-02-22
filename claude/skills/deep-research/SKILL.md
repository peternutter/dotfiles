---
name: deep-research
description: Deep multi-source research using parallel sub-agents. Use when asked to research topics requiring comprehensive analysis, product comparisons, market research, technical investigations, or any query that benefits from 20+ sources. Produces cited reports saved to the notes folder.
metadata: {"openclaw":{"emoji":"🔬","category":"research"}}
---

# Deep Research

Perform thorough, multi-source research by spawning parallel sub-agents that each investigate different aspects of a topic, then synthesize findings into a comprehensive cited report.

## When to Use

- User asks to "research", "deep dive", "compare", or "investigate" something
- Topic benefits from 20+ sources and multiple angles
- Product comparisons, market analysis, technical reviews, academic surveys

## Workflow

### Step 1: Decompose the Query

Break the research question into 4-6 independent sub-questions. Each will be handled by a separate sub-agent.

Example for "Best GaN USB-C chargers":
1. Top-rated GaN chargers from review sites (Wirecutter, Tom's Hardware, RTINGS)
2. Reddit/forum user experiences and complaints
3. Technical specs comparison (wattage, ports, size, weight)
4. Pricing and EU availability
5. Reliability and safety certifications
6. Recent releases and upcoming models

### Step 2: Spawn Parallel Sub-Agents

For each sub-question, spawn a sub-agent:

```
sessions_spawn(
  task: "Research sub-question: [SPECIFIC QUESTION]
  
  Do 3-5 web searches with different keyword variations.
  For the most relevant results, fetch the full page content with web_fetch.
  
  Write your findings to: /home/node/.openclaw/workspace/notes/research-temp/[slug]-[N].md
  
  Format:
  # [Sub-question]
  ## Key Findings
  - Finding 1 (Source: [name](url))
  - Finding 2 (Source: [name](url))
  ## Detailed Notes
  [Longer notes with quotes and data]
  ## Sources
  1. [Title](url) - [one-line summary]",
  label: "research-[slug]-[N]"
)
```

Spawn all sub-agents at once (they run in parallel, up to maxConcurrent).

### Step 3: Synthesize

Once all sub-agents complete, read all temp files from `notes/research-temp/` and synthesize into a final report.

Save to: `notes/[topic-slug]-research.md`

### Report Structure

```markdown
# [Topic]: Research Report
*Generated: [date] | Sources: [N] | Method: Deep Research (parallel sub-agents)*

## Executive Summary
[3-5 sentences with the key takeaways]

## 1. [Major Theme/Category]
[Findings with inline citations]
- Key point ([Source](url))
- Data point ([Source](url))

## 2. [Next Theme]
...

## Recommendations
[If applicable - ranked picks, action items, or conclusions]

## Methodology
- [N] sub-agents searched [M] total queries
- [X] sources analyzed
- Sub-questions investigated: [list]

## All Sources
1. [Title](url) - [summary]
2. ...
```

### Step 4: Clean Up

Delete the temp files in `notes/research-temp/` after synthesis.

### Step 5: Deliver

- Post executive summary + recommendations in chat
- Mention the full report path for details
- If the user is on Telegram, keep the chat summary concise (no tables)

## Quality Rules

1. Every claim needs a source. No unsourced assertions.
2. Cross-reference: if only one source says it, flag as unverified.
3. Prefer recent sources (last 12 months).
4. Acknowledge gaps honestly.
5. No hallucination. "Insufficient data" is better than making things up.
6. De-duplicate across sub-agents (they may find the same sources).

## Configuration

- Sub-agents: 4-6 per research task
- Searches per sub-agent: 3-5
- Full page reads per sub-agent: 2-3 (most promising results)
- Target: 20-40 unique sources total
- Output: `/home/node/.openclaw/workspace/notes/[slug]-research.md`
- Temp: `/home/node/.openclaw/workspace/notes/research-temp/`
