---
name: deep-research
description: Performs deep web research on a topic using diverse public sources, verifies claims across reliable websites, and produces a high-quality synthesized final answer with citations. Use when the user asks for deep research, web research, market research, technical research, competitive analysis, current information, or the best answer from internet sources.
---

# Deep Research

Use this skill when the user wants a thorough, web-grounded answer rather than a quick response.

## Research Workflow

1. Restate the research goal in one sentence.
2. If the topic is too broad or the expected output is unclear, ask one focused clarification. Otherwise proceed.
3. Build a search plan with 3-6 angles, such as:
   - official or primary sources
   - recent news and analysis
   - technical documentation or papers
   - government, standards, legal, or regulatory sources
   - company pages, filings, changelogs, or product docs
   - expert blogs, forums, GitHub issues, benchmarks, or community reports
4. Use `WebSearch` for broad discovery and `WebFetch` for sources that look useful.
5. Prefer primary, official, recent, and technically specific sources. Use secondary sources for context, not as the only proof.
6. Cross-check important claims with at least two independent sources when possible.
7. Track source quality, publication date, author or organization, and any conflicts between sources.
8. Do not cite sources you did not inspect. Do not invent facts, dates, numbers, quotes, or URLs.

## Source Strategy

Use a mix of source types when relevant:

- Official documentation, API references, standards, regulatory pages, or product pages
- Academic papers, whitepapers, patents, and technical reports
- Government datasets, court records, financial filings, and policy documents
- Reputable journalism, industry analysis, and analyst reports
- GitHub repositories, release notes, issue trackers, mailing lists, and forums
- Company blogs, engineering blogs, case studies, pricing pages, and changelogs
- Reviews, benchmarks, social discussions, and user reports when sentiment or adoption matters

Treat low-authority sources as signals to investigate, not final evidence.

## Analysis Standards

- Separate facts from interpretation.
- Call out uncertainty, outdated information, weak evidence, or conflicting claims.
- Include dates for time-sensitive claims.
- Compare alternatives using criteria that matter to the user's question.
- Prefer a direct recommendation when the evidence supports one.
- If the web results are thin, say so and explain the best available conclusion.

## Final Output

Structure the answer for decision-making:

```markdown
## Executive Summary
[Best answer in 2-5 concise bullets or one short paragraph.]

## Key Findings
- [Finding with source link]
- [Finding with source link]
- [Finding with source link]

## Analysis
[Synthesize what the evidence means. Explain tradeoffs, patterns, and contradictions.]

## Recommendation
[Clear recommendation or best answer, with assumptions.]

## Sources
- [Source title](URL) — why it matters
- [Source title](URL) — why it matters
```

For small questions, compress the structure. For complex or data-heavy topics, add sections such as methodology, comparison, timeline, risks, or open questions.
