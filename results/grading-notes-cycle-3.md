# Grading Notes — Cycle 3

## Near-bar patterns observed across candidates

### Pattern 1: Well-structured task descriptions (most common false-positive risk)
Prompts that are detailed, technical, and well-organised but contain no original insight — e.g. "Build a Node.js backend with these modules: X, Y, Z". These look impressive but the structure came from the user's prior reading, not genuine steering of the LLM.

### Pattern 2: Reactive constraint clarifications
Short prompts that tighten a constraint already implied by the LLM's output (e.g. "make it lowercase", "no edge functions"). These are above-bar only when the constraint comes from the user's own domain knowledge and materially redirects the trajectory.

### Pattern 3: Decision queries that trigger strong LLM responses
User asks a well-framed question → LLM gives a great answer. The outcome is good but the insight is the LLM's, not the user's. These are near-bar at best.

### Pattern 4: Thin reactive sparks
Very short user observations (1-2 sentences) that the LLM develops into something substantial. The user's contribution was minimal — the LLM did the heavy lifting. Near-bar unless the spark itself was genuinely non-obvious.

## Rubric criteria hardest to apply consistently
1. **"Key insight from user not LLM"** — hardest to judge. When the user asks a sharp question that forces the LLM to produce insight, who owns the insight?
2. **"Correct direction"** — requires knowing the domain. Reviewers may not recognise wrong directions in unfamiliar codebases.
3. **"Efficiency"** — hard to penalise when the repeated prompts were each individually reasonable responses to LLM failures.

## Above-bar counts (final)
- Abdul: 7
- Arleif: 13
- Bharath: 6
- Vidhusan: 5
