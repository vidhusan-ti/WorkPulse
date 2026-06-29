# WorkPulse: Pipeline Processing Approaches

> Architecture research for **how the grading pipeline runs** — the processing/performance layer.
> Each approach covers the full SND->IOAS->CTA->EJAD 4-stage pipeline unless noted.

---

### Approach 1: Synchronous Blocking

**How it works:** When a new window is detected, the system immediately runs all 4 pipeline stages sequentially and blocks the UI until the full grade is returned before accepting the next window.

**Pros:**
- Simplest possible implementation — no queues, no async coordination
- Result is always complete before the next window is processed
- Easy to debug and reason about

**Cons:**
- User waits 3–8 seconds per window with no feedback — feels frozen
- If a window is detected mid-conversation, all subsequent windows pile up
- No ability to show partial progress
- A single slow LLM call stalls everything

**Complexity:** Low
**Latency:** 3–8 seconds (full pipeline, blocking)

---

### Approach 2: Async Background Grading with Notification

**How it works:** Window detection enqueues a grading job immediately and returns; the pipeline runs in the background, and when all 4 stages complete, a notification/badge is pushed to the UI.

**Pros:**
- UI never freezes — user can keep working
- Simple mental model: "grading happening in background"
- Easy to implement with a simple worker pattern (Promise queue, worker thread)
- Multiple windows can be detected while one is grading

**Cons:**
- User sees no progress during the 3–8 second wait
- Results arrive all-at-once, potentially out of order with their workflow
- If the user finishes a session quickly, grades arrive after they've moved on

**Complexity:** Low–Medium
**Latency:** 3–8 seconds (non-blocking; result appears asynchronously)

---

### Approach 3: Streaming Stage-by-Stage Grading

**How it works:** Each pipeline stage (SND->IOAS->CTA->EJAD) runs sequentially, but the UI updates progressively as each stage completes — showing a partial score/badge after each LLM call returns.

**Pros:**
- Users get feedback within ~1–2 seconds (first stage result)
- Feels fast and alive — progress indicators are honest
- Early stages can signal "not worth continuing" before wasting full pipeline cost
- Natural fit for a live dashboard / score ticker

**Cons:**
- UI must handle partial/updating state gracefully (can cause flicker or confusion)
- More complex UI state management (scores update 4 times per window)
- Still makes all 4 LLM calls unless early-exit logic is added

**Complexity:** Medium
**Latency:** ~1–2 seconds to first stage result; ~3–8 seconds to final score

---

### Approach 4: FIFO Queue (One Window at a Time)

**How it works:** All detected windows are placed in a first-in-first-out queue; a single worker processes them in order, fully grading one window before starting the next.

**Pros:**
- Preserves chronological ordering of results
- Predictable resource usage — never more than one pipeline running at once
- Simple to implement with a standard queue data structure
- Avoids LLM rate-limit issues from concurrent calls

**Cons:**
- Under heavy detection bursts, queue depth grows and lag compounds
- The most recent window — which the user cares about most — may wait behind older ones
- No prioritization; a boring early window blocks a critical recent one

**Complexity:** Low–Medium
**Latency:** (N x 3–8s) where N = queue depth at time of detection; worst case minutes

---

### Approach 5: Priority Queue (Most Recent First)

**How it works:** Detected windows enter a priority queue ordered by recency; the worker always picks the newest ungraded window, deprioritizing older ones when new work arrives.

**Pros:**
- The most recent window — what the user just did — grades first
- Older windows grade eventually during idle periods
- Keeps the dashboard current with the user's active work
- Simple priority inversion avoids the "stale queue" problem

**Cons:**
- Old windows may starve if the user works continuously (never grade older windows)
- Out-of-order results can confuse a timeline-style UI
- Slightly more complex than FIFO queue

**Complexity:** Medium
**Latency:** ~3–8 seconds for the newest window (even under load)

---

### Approach 6: Batched Grading (Periodic Flush)

**How it works:** Detected windows accumulate in a buffer; every N minutes (e.g., 5 min), the system grades all buffered windows in one batch, potentially combining context or parallelizing calls.

**Pros:**
- Significantly reduces LLM call overhead if batch context can be shared
- Great for end-of-session reviews where real-time is not needed
- Can parallelize all windows in the batch with a single burst
- Easy to implement as a cron-style scheduled flush

**Cons:**
- Not real-time — feedback delayed by up to N minutes
- Users do not know their score while actively working
- Batch results arrive all at once, which can be overwhelming
- Does not support "live coaching" use cases

**Complexity:** Low–Medium
**Latency:** Up to N minutes (configurable; default ~5 min)

---

### Approach 7: SND Fast-Path (Local Rule-Based Pre-filter)

**How it works:** Stage 1 (SND — Signal/Noise Detection) is replaced with a fast local heuristic (keyword matching, token length checks, regex patterns) that can instantly reject obviously below-bar windows before any LLM call is made.

**Pros:**
- Zero latency and zero cost for clear rejections (e.g., one-word prompts, copy-paste dumps)
- Reduces LLM calls by 20–50% on typical transcripts
- Can run synchronously on the detection thread without queuing
- Combines well with any other approach as a pre-filter layer

**Cons:**
- Local heuristics miss nuanced cases — false positives and false negatives
- Requires maintaining a separate rule set that may need tuning
- Does not improve latency for windows that pass the fast-path (still 3–8s)
- Creates a two-tier system that can feel inconsistent

**Complexity:** Low (heuristics) to Medium (trained local classifier)
**Latency:** <100ms for rejections; ~3–8s for windows passing fast-path

---

### Approach 8: Semantic Caching (Skip Re-grading Near-Duplicate Windows)

**How it works:** Before grading, each new window's content is hashed (or embedded) and compared against a local cache of recently graded windows; near-duplicate prompts return the cached grade instantly without LLM calls.

**Pros:**
- Instant results for repeated or similar prompts (common in iterative dev sessions)
- Significant cost savings when users try slight variations of the same question
- Cache lookup is O(1) for exact hashes, fast for embedding similarity
- Fully transparent to the rest of the pipeline

**Cons:**
- Cache management overhead (size limits, TTL, invalidation strategy)
- Embedding-based similarity requires a local embedding model or API call
- Two "similar but different" windows may get the same grade incorrectly
- Cold start: cache is empty at session start

**Complexity:** Low (exact hash) to Medium (semantic similarity with embeddings)
**Latency:** <50ms for cache hits; normal 3–8s for misses

---

### Approach 9: Lightweight Local Model First (Escalation Pattern)

**How it works:** A small, fast local model (e.g., Ollama + Phi-3-mini or similar) grades the window first in ~200–500ms; if the local model is confident, that grade is used; only borderline or high-stakes windows escalate to the full Claude pipeline.

**Pros:**
- Sub-second results for ~60–80% of windows (the clear cases)
- Dramatic cost reduction — Claude only handles ambiguous cases
- Local model can be fine-tuned on WorkPulse rubric data over time
- Works offline; no API dependency for routine grades

**Cons:**
- Requires running a local model (Ollama, llama.cpp) — adds system requirements
- Local model accuracy is lower; escalation threshold is hard to calibrate
- Two different graders may produce inconsistent scores across sessions
- Higher complexity to set up, test, and maintain

**Complexity:** High
**Latency:** ~200–500ms for local-confident grades; ~3–8s for escalated grades

---

### Approach 10: Scheduled End-of-Session Grading

**How it works:** No grading happens during the working session; all detected windows are stored locally and graded in a single batch at session end (e.g., when the user closes Cursor or runs a manual "grade session" command).

**Pros:**
- Zero runtime overhead during the working session — no latency impact
- Full session context available (can grade windows relative to each other)
- Batch processing enables parallelism and potential prompt compression
- Simple, predictable user experience: "open report when you're done"

**Cons:**
- Not real-time at all — no live coaching or in-session feedback
- Users cannot course-correct mid-session based on grades
- Session detection (when does a session "end"?) can be ambiguous
- Completely breaks the real-time monitoring value proposition

**Complexity:** Low
**Latency:** Full session delay (minutes to hours); results available post-session

---

### Approach 11: Differential Grading (Only New Turns Since Last Check)

**How it works:** Each grading cycle compares the current transcript state against the last known checkpoint; only turns that are genuinely new since the last cycle are submitted for grading, avoiding re-processing existing content.

**Pros:**
- Eliminates redundant re-grading of already-processed windows
- Efficient for long sessions where the same file grows incrementally
- Naturally handles Cursor's append-only JSONL format
- Reduces API calls proportionally to session length

**Cons:**
- Requires maintaining a persistent checkpoint per file (cursor position or window ID)
- Edge cases: if checkpoint state is lost, may re-grade everything or miss windows
- Does not improve latency for genuinely new windows (still 3–8s)
- Complexity increases if Cursor ever rewrites or compacts files

**Complexity:** Low–Medium
**Latency:** Same as underlying approach for new windows; ~0ms for already-graded content

---

### Approach 12: Concurrent Pipeline Stages (Parallel LLM Calls)

**How it works:** Where pipeline stages are independent, they are executed in parallel (e.g., IOAS and CTA both run concurrently after SND passes), reducing total wall-clock time by running multiple LLM calls simultaneously.

**Pros:**
- Reduces total pipeline latency from sum-of-stages to max-of-stages
- If 3 of 4 stages can parallelize, total time drops from ~6s to ~2–3s
- No change to grading logic or rubric — purely a scheduling optimization
- Combines well with streaming (show results as each parallel call returns)

**Cons:**
- Not all stages can parallelize — SND must run before IOAS/CTA in most rubric designs
- Concurrent LLM calls multiply rate-limit exposure
- More complex orchestration: need to handle partial failures and timeouts
- Cost is unchanged (same number of LLM calls, just faster)

**Complexity:** Medium
**Latency:** ~2–4 seconds (depending on parallelizable stage count)

---

### Approach 13: Human-in-the-Loop Gate

**How it works:** After detecting a window, the system shows it to the user with a quick "Grade this? [Yes / Skip / Later]" prompt; full LLM grading only runs on explicitly approved windows, giving the user control over what gets graded and when.

**Pros:**
- Zero wasted LLM calls on windows the user does not care about
- User remains in control — no surprise background activity
- Surfaces the grading process, making it feel transparent and trustworthy
- Useful as a learning tool: user decides which interactions are grade-worthy

**Cons:**
- Requires constant user attention — interrupts flow rather than running silently
- Defeats the purpose of automated real-time monitoring
- Users will likely just click "Yes" to everything, adding friction with no benefit
- Latency depends entirely on how quickly the user responds

**Complexity:** Medium (UI gate + approval flow)
**Latency:** Human decision time (seconds to minutes) + 3–8s for grading

---

## Summary Matrix

| # | Approach | Complexity | Latency to First Result | Real-time? | Cost Impact |
|---|---|---|---|---|---|
| 1 | Synchronous Blocking | Low | 3-8s (blocking) | Blocks UI | Baseline |
| 2 | Async Background + Notify | Low-Med | 3-8s (non-blocking) | UI free | Baseline |
| 3 | Streaming Stage-by-Stage | Medium | ~1-2s (partial) | Progressive | Baseline |
| 4 | FIFO Queue | Low-Med | 3-8s x queue depth | UI free | Baseline |
| 5 | Priority Queue (newest first) | Medium | ~3-8s (newest) | Current | Baseline |
| 6 | Batched Periodic Flush | Low-Med | Up to N minutes | Delayed | Reduced |
| 7 | SND Fast-Path Pre-filter | Low-Med | <100ms (rejects) | Partial | -20-50% |
| 8 | Semantic Caching | Low-Med | <50ms (hits) | Cache hits | Reduced |
| 9 | Local Model Escalation | High | ~200-500ms (local) | Fast | -60-80% |
| 10 | End-of-Session Batch | Low | Post-session | No real-time | Reduced |
| 11 | Differential Grading | Low-Med | Same as base | Efficient | Reduced |
| 12 | Concurrent Parallel Stages | Medium | ~2-4s | Faster | Unchanged |
| 13 | Human-in-the-Loop Gate | Medium | Human + 3-8s | Interrupted | Reduced |

---

*Generated for WorkPulse architecture research — pipeline/processing layer.*
