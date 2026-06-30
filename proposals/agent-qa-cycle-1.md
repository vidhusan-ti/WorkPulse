# Agent QA Cycle 1 — WorkPulse Pipeline QA Report

**Date:** 2026-06-29  
**Agent:** QA Agent (agent-qa-cycle-1)  
**Scope:** Full review of `src/pipeline/`, `src/extractor.py`, `src/watcher.py`, `src/grader.py`, `src/persister.py`, `src/monitor.py`, and all tests.

---

## Test Results

**All 89 tests pass.** ✅

```
89 passed in 9.14s
```

No failures. Test coverage is strong for the pipeline stages (SND, IOAS, CTA, EJAD), the orchestrator, persister, extractor, and portfolio writer.

---

## Bugs Found

### BUG-1 — `persist_grade` crashes with `FileNotFoundError` when path has no directory component
**File:** `src/persister.py`, line 96  
**Severity:** Medium — crashes if `graded_events_file` is set to a bare filename like `"events.jsonl"` with no directory prefix.

```python
# Bug:
os.makedirs(os.path.dirname(graded_events_file), exist_ok=True)
# os.path.dirname("events.jsonl") == "" → os.makedirs("") raises FileNotFoundError
```

**Fix applied:**
```python
_dir = os.path.dirname(graded_events_file)
if _dir:
    os.makedirs(_dir, exist_ok=True)
```

---

### BUG-2 — `format spec ':.3f' crashes on fallback string `'n/a'` in `grader_v2.py`
**File:** `src/pipeline/grader_v2.py`, line 353  
**Severity:** Low — only reachable if `s2["score"]` key is missing (shouldn't happen in practice since all code paths set it, but the default value `'n/a'` is a string, which crashes the f-string format spec).

```python
# Bug:
f"Intent alignment: {s2.get('score', 'n/a'):.3f}. "
# If s2 somehow lacks 'score', 'n/a' is a string → TypeError at runtime
```

**Fix applied:**
```python
f"Intent alignment: {float(s2.get('score', 0.0)):.3f}. "
```

---

### BUG-3 — `SentenceTransformer` model re-loaded on every Stage 1 call (performance bug)
**File:** `src/pipeline/stage1_snd.py`, `_embedding_novelty()` function  
**Severity:** Medium — every window graded triggers a fresh `SentenceTransformer("all-MiniLM-L6-v2")` load (~200–500ms model loading overhead per call). For a busy coding session this slows the monitor loop noticeably.

```python
# Bug: model reloaded on every call
def _embedding_novelty(user_prompt, prior_texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)  # ← fresh load every time
    ...
```

**Fix applied:** Added a module-level `_ST_MODEL_CACHE` variable. The model is loaded once and reused:

```python
_ST_MODEL_CACHE: Optional[Any] = None

def _embedding_novelty(user_prompt, prior_texts):
    global _ST_MODEL_CACHE
    if _ST_MODEL_CACHE is None:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL_CACHE = SentenceTransformer(EMBEDDING_MODEL)
    model = _ST_MODEL_CACHE
    ...
```

---

### BUG-4 — `_has_follow_up_turns` matches on first occurrence of focal text, not window position
**File:** `src/pipeline/stage3_cta.py`, `_has_follow_up_turns()` function  
**Severity:** Low — edge case. If the same user prompt text appears twice in the turns list, `found_focal = True` is set on the first match. In a sliding window that starts at the second occurrence of that text, `_has_follow_up_turns` will incorrectly identify follow-up turns from after the *first* occurrence.

**Impact:** In practice, windows are small (3 turns) and duplicate user prompts are rare enough that this doesn't affect production output. However, it could produce an incorrect `has_follow_up=yes` signal in the LLM prompt for Stage 3 when no actual follow-up exists in the window.

**No fix applied** — requires threading window position into Stage 3. See Needs Human Review.

---

## Gaps

### GAP-1 — `data/manual_rubric.md` is NOT used by the v2 pipeline
The `grade_window_v2()` function accepts `rubric_path` as a parameter and the docstring says it's "used for context", but it is **never read or injected** into any Stage 2/3/4 LLM prompt. The rubric is only used by the legacy `grader.py` (v1 grader).

- Stage 2/3/4 operate entirely from hardcoded system prompts embedded in each stage file.
- `manual_rubric.md` contains the original human-authored rubric criteria but has zero influence on v2 grading.
- `rubric_path` is a vestigial parameter in `grade_window_v2`.

**Recommendation:** Either (a) inject rubric excerpts into Stage 2/3/4 prompts, or (b) officially document v2 is prompt-driven and remove/deprecate `rubric_path`. Currently it creates false expectation.

---

### GAP-2 — No test for `persist_grade` with bare filename (the BUG-1 scenario)
**File:** `tests/test_persister.py`  
The test suite calls `persist_grade` with a full temp file path but never tests the edge case of a bare filename without a directory component.

---

### GAP-3 — `load_config` in `monitor.py` has no error handling
**File:** `src/monitor.py`, `load_config()` function  
```python
def load_config(config_path: str = "config/settings.json") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
```
Missing or corrupt config raises unhandled `FileNotFoundError` / `json.JSONDecodeError`. The `main()` entry point guards against missing files, but the function itself has no safety net.

---

### GAP-4 — Watcher polling swallows all exceptions silently
**File:** `src/watcher.py`, `_poll_loop()` method  
```python
except Exception:
    pass  # ← silently swallows all errors including PermissionError, OOM, etc.
```
Any error in the poll loop is silently dropped with no logging. Should at minimum `logger.warning(...)` the exception.

---

### GAP-5 — `_normalise_turn` silently drops non-dict content blocks in Format B
**File:** `src/extractor.py`, `_normalise_turn()`  
In Format B, if any content block is a string instead of a `{"type": "text", "text": "..."}` dict, it's silently skipped. Likely harmless, but can cause silent loss of turn content if Cursor ever emits mixed content block types.

---

### GAP-6 — `_extract_dissenter_confidence` uses fragile regex parsing
**File:** `src/pipeline/grader_v2.py`, `_extract_dissenter_confidence()`  
```python
match = re.search(r"confidence=(\d+\.\d+)", final_reasoning)
```
Parses dissenter confidence from a free-text string that grader_v2 itself wrote. Tightly coupled to internal formatting — silently returns `None` (falling back to `outstanding_portfolio`) if the format ever changes. Dissenter confidence should be stored as a first-class field in the stage4 result dict.

---

### GAP-7 — No integration test with a real JSONL file
The test suite is entirely unit tests with mocked LLM calls and synthetic windows. No test reads an actual JSONL file from `data/` or `results/` to verify the full file → transcript → windows → graded output pipeline. Listed as a next step in PROJECT_STATE.md.

---

### GAP-8 — `deduplicate_session_grades` silently drops grades with empty hash
**File:** `src/persister.py`  
```python
hash_key = grade.get("focal_prompt_hash", "")
if not hash_key:
    continue  # grades without hash are silently discarded
```
Grades without a `focal_prompt_hash` (e.g. graded by v1 grader) are silently lost. No test covers this scenario.

---

### GAP-9 — `grader.py` (v1) uses `print()` for errors instead of `logging`
**File:** `src/grader.py`  
All other components use `logging`. v1 uses `print()`, making v1 errors appear on stdout regardless of logging configuration.

---

### GAP-10 — `run_setup` wizard config does not include `use_pipeline_v2`
**File:** `main.py`, `run_setup()` wizard  
Setup wizard output omits `"use_pipeline_v2": true`. Users on the wizard path still get v2 (monitor defaults to `True`), but the saved config doesn't document the actual behavior. Minor but confusing.

---

## Quick Fixes Applied

| Fix | File | Description |
|-----|------|-------------|
| BUG-1 | `src/persister.py` line 96 | Guard `os.makedirs` against empty dirname |
| BUG-2 | `src/pipeline/grader_v2.py` line 353 | Replace `:.3f` on `'n/a'` default with `float(..., 0.0)` |
| BUG-3 | `src/pipeline/stage1_snd.py` | Module-level `_ST_MODEL_CACHE` to avoid re-loading SentenceTransformer every call |

All 89 tests still pass after fixes.

---

## Needs Human Review

### REVIEW-1 — Rubric gap (GAP-1) architectural decision
Should `manual_rubric.md` be injected into v2 LLM prompts? Options:
- **Option A:** Inject rubric as context in Stage 2 and Stage 4 prompts.
- **Option B:** Accept that v2 prompts ARE the rubric; deprecate `rubric_path` parameter.
- **Option C:** Add a rubric validation step post-Stage 4.

### REVIEW-2 — `_extract_dissenter_confidence` should be a first-class field (GAP-6)
Stage4 result dict should store `dissenter_confidence: float` directly. Requires small API change to `run_stage4` return dict.

### REVIEW-3 — `_has_follow_up_turns` positional matching (BUG-4)
Fix requires passing the focal turn's index (not just text) into Stage 3. Cleanest fix: add `focal_index: Optional[int]` parameter to `run_stage3`. Requires test updates.

### REVIEW-4 — Stage 2 below-bar getting coaching — is that intended?
`grader_v2.py` calls `_get_coaching` for Stage 2 failures (producing `below_bar` results with coaching). This is an extra LLM call for every Stage 2 failure. The original design only mentioned coaching for near-bar. Confirm this is intentional and worth the cost.

### REVIEW-5 — Watcher runs both watchdog AND polling simultaneously
**File:** `src/watcher.py`  
When watchdog is available, both run concurrently. Events may be delivered twice (deduplicated by the `_pending_paths` set, so not a correctness bug, but wasteful). Recommend: only run polling when watchdog is unavailable.

---

## Summary

| Category | Count |
|----------|-------|
| Tests passing | 89/89 ✅ |
| Bugs found | 4 |
| Bugs fixed | 3 (BUG-1, BUG-2, BUG-3) |
| Bugs deferred | 1 (BUG-4 — needs architectural review) |
| Gaps identified | 10 |
| Items for human review | 5 |

The pipeline logic is solid. The biggest structural gap is that `manual_rubric.md` has no influence on v2 grading — this should be a conscious decision, not an oversight.
