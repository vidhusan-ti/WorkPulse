# WorkPulse Improvement Proposals
### Agent R — Cycle 2
#### Focus: Edge Cases, UX Improvements, False-Negative Reduction

Cycle 2 builds on the 4-stage pipeline v2 (SND→IOAS→CTA→EJAD). These proposals
address gaps identified through implementation, testing, and performance analysis.

---

## Proposal 12: Sliding Window Overlap De-duplication (SWOD)

### Problem
WorkPulse uses a sliding window approach, meaning adjacent windows share turns.
A single brilliant user prompt (turn N) will appear in multiple overlapping windows:
- Window: [N-1, N, N+1]
- Window: [N, N+1, N+2]
- Window: [N+1, N+2, N+3]

This causes false inflation: the same prompt contributes to 2-3 windows, potentially
generating multiple above-bar grades for a single user action.

### Proposed Solution
Add a deduplication layer after grading that:
1. Compares focal user prompts across all graded windows in a session
2. If two windows share the same focal user turn (same text/hash), keeps only the
   highest-scoring grade
3. Generates a session-level "unique above-bar moments" count rather than window count
4. Tags duplicate windows with `deduplicated: true` in the trace for transparency

### Implementation Details
- Add `focal_prompt_hash` field to every graded result
- Post-processing step in `persister.py` before writing to `graded_events.jsonl`
- Hash: `sha256(focal_user_prompt.strip().lower())[:16]`
- Session boundary: all windows from the same transcript file

### Impact
- **False positive reduction:** Prevents 2-3x inflation of above-bar counts
- **Portfolio quality:** Above-bar portfolio entries represent distinct moments
- **Score calibration:** Per-session metrics become meaningful

### Edge Cases Handled
- Long prompts edited slightly across windows: fuzzy hash with normalized text
- Two distinct good prompts in adjacent windows: both preserved (different hashes)

### Effort: Low — post-processing only, no pipeline changes
### Priority: High (correctness issue, not just quality)

---

## Proposal 13: Stage 1 Semantic Novelty Calibration via Embedding Similarity Distribution

### Problem
The current Stage 1 Jaccard fallback uses a fixed threshold (0.25) that was set
manually. This threshold:
- May be too lenient for long technical prompts (many shared domain words)
- May be too strict for very short but genuinely novel prompts
- Is not calibrated against real above-bar/below-bar labeled examples

The root cause: Jaccard distance is a lexical metric that ignores semantic similarity.
A user could paraphrase LLM output with completely different words and pass Stage 1.

### Proposed Solution
Implement a calibrated Stage 1 that:
1. **Primary path:** sentence-transformers cosine similarity (already implemented)
2. **Calibration data:** Use labeled examples from `graded_events.jsonl` to find
   the novelty score distribution for known above-bar vs known below-bar windows
3. **Dynamic threshold:** Set NOVELTY_THRESHOLD at the 15th percentile of
   above-bar scores (false negative floor) rather than arbitrary 0.25
4. **Jaccard calibration fix:** Supplement Jaccard with bigram overlap to catch
   paraphrase-by-synonym patterns

### Implementation
```python
# In stage1_snd.py
def _bigram_jaccard_novelty(user_prompt: str, prior_texts: List[str]) -> float:
    """Bigram Jaccard is more robust to synonym paraphrasing."""
    user_bigrams = _bigrams(_tokenize(user_prompt))
    distances = [_jaccard_distance(user_bigrams, _bigrams(_tokenize(pt))) 
                 for pt in prior_texts]
    return min(distances)
```

### Impact
- **False negative reduction:** Semantic paraphrasers currently pass Stage 1 incorrectly
- **Threshold stability:** Data-driven threshold adapts to user's writing style

### Effort: Medium — requires labeled data pipeline
### Priority: Medium (quality, not correctness)

---

## Proposal 14: Context-Aware Window Sizing (CAWS)

### Problem
WorkPulse currently grades fixed-size windows (3 turns). This is arbitrary and
creates two failure modes:
1. **Too small:** A brilliant user prompt at turn N is judged without enough context.
   The LLM's response at N-1 that the user is reacting against isn't included.
2. **Too large:** A 5-turn window dilutes the focal turn's signal with irrelevant
   prior context, making it harder to attribute quality to the focal user prompt.

### Proposed Solution
Implement context-aware window sizing:
1. **Minimum context:** Always include 1 prior assistant turn before the focal user turn
   (captures what the user is reacting to)
2. **Maximum context:** Cap at 5 turns to avoid LLM context confusion
3. **Dynamic expansion:** If Stage 3 (CTA) requests "no follow-up turns" context,
   attempt to include the next turn by fetching from transcript if available
4. **Anchor turn:** Mark the focal user turn explicitly in window metadata so stages
   always know which turn they're grading

### Implementation Details
```python
# In extractor.py
def build_window(turns, focal_index, min_before=1, max_total=5):
    start = max(0, focal_index - min_before)
    end = min(len(turns), focal_index + (max_total - (focal_index - start)))
    return {
        "turns": turns[start:end],
        "focal_index": focal_index - start,  # 0-based index within window
    }
```

### Impact
- **False negative reduction:** Novel corrections judged with prior context
- **Stage 3 quality:** CTA has follow-up context more often
- **Below-bar accuracy:** Confirmations/approvals have the LLM context they're approving

### Effort: Medium — affects extractor.py and all stage contracts
### Priority: Medium (structural quality improvement)

---

## Proposal 15: Prompt Fingerprint Anti-Gaming Detection

### Problem
As WorkPulse scores become visible to users, some may learn to write prompts that
pattern-match to above-bar signals without genuine insight:
- Starting prompts with "Actually, I think we should..." (correction-like language)
- Always including "because..." clauses (simulates constraint specification)
- Using technical jargon without substance

These gaming patterns represent a subtle false-positive problem that will grow as
the tool is used more widely.

### Proposed Solution
Add a "fingerprint" detector to Stage 4's dissenter that explicitly checks for
surface-level gaming signals:
1. **Structural mimicry:** Prompt has above-bar structure but LLM-supplied content
2. **Jargon without substance:** High technical word density but low semantic specificity
3. **Template patterns:** Common above-bar phrase patterns without matching content

Implementation: Add 3 specific questions to the Stage 4 dissenter:
```
- Does this prompt have above-bar STRUCTURE but LLM-supplied CONTENT?
  (e.g., "Actually, X is wrong because Y" — but X and Y came from the LLM?)
- Is the technical language specific to the user's context, or generic domain terms?
- Is the correction/pushback based on something only the user would know,
  or could the LLM have generated this correction itself?
```

### Impact
- **False positive reduction:** Catches structural gaming
- **Calibration:** Dissenter becomes more sensitive to the "LLM-supplied core insight" anti-pattern
- **Long-term robustness:** Maintains above-bar rarity and value

### Effort: Low — prompt-only change to Stage 4 dissenter
### Priority: Medium (important for long-term signal quality)

---

## Proposal 16: Portfolio Momentum Score (PMS)

### Problem
WorkPulse currently grades each window independently. This ignores an important
signal: **trajectory over a session**. A user who produces 3 above-bar prompts in
a row on a complex problem is demonstrating something qualitatively different from
a user who produces 1 above-bar prompt scattered among 50 below-bar ones.

Additionally, near-bar windows that cluster together may collectively represent
above-bar thinking broken across multiple turns (user built up to a great prompt).

### Proposed Solution
Add a session-level "Portfolio Momentum Score" computed after all windows are graded:

1. **Streak bonus:** 3+ consecutive above-bar/near-bar windows get a momentum flag
2. **Cluster detection:** Near-bar windows within 3 turns of each other are analyzed
   for whether they collectively represent a single above-bar insight broken up
3. **Density metric:** above-bar count / total windows (filtered for min session length)
4. **Session report:** Includes "peak momentum" periods with their timestamps

Implementation:
```python
# In persister.py or a new src/portfolio_analyzer.py
def compute_momentum(graded_windows: List[Dict]) -> Dict:
    streaks = find_quality_streaks(graded_windows, min_length=3)
    clusters = find_near_bar_clusters(graded_windows, proximity=3)
    density = compute_quality_density(graded_windows)
    return {
        "streak_periods": streaks,
        "near_bar_clusters": clusters,
        "quality_density": density,
        "momentum_peak": max(streaks, key=lambda s: s["length"]) if streaks else None,
    }
```

### Impact
- **False negative reduction:** Near-bar clusters may represent above-bar thinking
- **User experience:** "You had a great run of prompts from 14:32-14:45" is more
  actionable than individual window scores
- **Coaching quality:** Can tell users "you almost had an above-bar streak here"
- **Portfolio building:** Momentum periods are prime portfolio candidates

### Edge Cases Handled
- Short sessions (< 5 windows): momentum not computed (insufficient data)
- All below-bar sessions: momentum is 0, no coaching inflation
- Mixed quality: momentum tracks the best contiguous run

### Effort: Medium — new module, no pipeline changes
### Priority: Medium-High (significant UX + false-negative reduction value)

---

## Summary Table

| # | Proposal | Category | Effort | Priority | Key Benefit |
|---|----------|----------|--------|----------|-------------|
| 12 | SWOD — Sliding Window De-duplication | Correctness | Low | **High** | Prevents 2-3x above-bar inflation |
| 13 | Stage 1 Calibration | Quality | Medium | Medium | Reduces paraphrase false-positives |
| 14 | Context-Aware Window Sizing | Quality | Medium | Medium | Better per-turn signal attribution |
| 15 | Prompt Fingerprint Anti-Gaming | Robustness | Low | Medium | Prevents structural gaming |
| 16 | Portfolio Momentum Score | UX | Medium | Medium-High | Session-level insight, false-neg reduction |

### Implementation Order (if approved)
1. **Proposal 12 (SWOD)** — correctness issue, quick win
2. **Proposal 16 (PMS)** — high user value, standalone module
3. **Proposal 15 (Anti-Gaming)** — prompt-only Stage 4 improvement
4. **Proposal 14 (CAWS)** — requires extractor contract changes
5. **Proposal 13 (S1 Calibration)** — requires labeled data pipeline

---

*Authored by Agent R (Cycle 2) — June 2026*
