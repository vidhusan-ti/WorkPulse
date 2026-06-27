# v2.6 Recurrence / Upstream-Causality Test Cases

Rubric: `data/high_bar_window_rubric.md` (`rubric_version: 2.6`)

Purpose: calibration examples for Arleif and Vidhusan where the grader must check whether the user is being rewarded for fixing a failure they caused earlier, or for repeatedly correcting the same agent failure instead of creating a durable prevention mechanism.

## Expected Rule

Do not treat every correction as portfolio-worthy. Before awarding `steering_recovery` or portfolio readiness, the grader must ask:

- Did the user's earlier prompt cause the bad result?
- Is this the same correction repeated across conversations?
- Did the user introduce a durable fix: rule, test, workflow change, prompt pattern, memory, source-of-truth cleanup, or guardrail?

If the answer is recurrence/self-inflicted and there is no durable fix, expected label should be `strong_highlight` or `below_bar`, not portfolio-ready.

## Test Case 1 - Arleif / Repeated Langfuse Source-Of-Truth Correction

- `source`: `D:\Downloads\20260618-114047\20260618-114047\.cursor\projects\workspaces-agno\agent-transcripts\11ab1d30-43a8-42cc-a958-c53ade325a16\11ab1d30-43a8-42cc-a958-c53ade325a16.jsonl`
- `reported_in`: `Arleif's.md`
- `condition`: recurring correction risk
- `expected_behavior`: the grader should not simply praise "do not duplicate Langfuse prompts." It must detect that this is a repeated operational failure and ask whether Arleif created a durable prevention mechanism.

**Conversation excerpt**

Previous context:

> The provisioner had failed because required session state was not persisted. The assistant traced local prompt files, Langfuse usage, and the risk that prompt instructions were not centralized.

User prompt:

> push the prompts to langfuse... check in langfuse verify they are there... delete local version. Remove all temporary scripts to push to langfuse. I DO NOT WANT 2 versions of the scripts and the risk that they go out of sync with each other, or that coder will accidentally read local version or fall back to them and we will spend weeks debugging why the product is not behaving like it should.

Assistant response:

> Deleted all five `agents/*/prompts/*.md` files... Provisioner now loads instructions from Langfuse... Runtime code paths only read Langfuse... no "read leader.md if Langfuse fails" path.

**v2.6 expected audit**

- `recurrence`: yes, the issue is repeated prompt-source drift.
- `upstream_causality`: not clearly self-inflicted in this window, but the repeated nature means the grader should not over-credit another one-off correction.
- `durable_fix`: partially yes: delete local prompt copies and temporary scripts.
- `expected_label`: `strong_highlight`, unless the transcript also proves a durable guardrail such as a CI check preventing local prompt files from reappearing.
- `expected_coaching`: "Do not keep correcting Langfuse drift manually. Add a CI assertion or repo rule that production prompt bodies cannot exist outside Langfuse."

## Test Case 2 - Arleif / Recovery After Bad Agent Path, Needs Prevention Check

- `source`: `D:\Downloads\20260618-114047\20260618-114047\.cursor\projects\workspaces-agno\agent-transcripts\85f482cd-872a-4f9e-9ac8-ef1eda014fb5.jsonl`
- `reported_in`: `Arleif's.md`
- `condition`: repeated workaround risk
- `expected_behavior`: the grader should not over-reward a cleanup decision if the stronger lesson is "stop fighting the same dynamic-prompt/chaining failure mode."

**Conversation excerpt**

Previous context:

> The assistant had shown capture evidence that Agno built updated workflow state but OpenAI did not receive it on chained calls, then proposed fixes such as re-sending instructions, injecting workflow state, or targeted OpenAI Responses workarounds.

User prompt:

> i think the right thing to do is kill chaining or kill dynamic system prompts and not fight this. There are other places where more stuff than state is changed in the prompt, our prompts are broken into many parts and then merged. I think short term we'll switch to non openai, maybe anthropic, and deal with this later. i prefer not doing dynamic prompts

Assistant response:

> Sensible call. Fighting the framework on two fronts (chaining + dynamic prompts) while prompts are already composed from fragments is net-negative complexity. Switching to Anthropic short-term unblocks you with zero architectural risk.

**v2.6 expected audit**

- `recurrence`: likely yes, because this is another case of avoiding repeated provider/framework workarounds.
- `upstream_causality`: unclear; the transcript should check whether earlier design choices created the dynamic-prompt/chaining conflict.
- `durable_fix`: partial: stop using dynamic prompts or chaining, but the durable invariant still needs to be captured as an ADR/test.
- `expected_label`: `strong_highlight`, not portfolio-ready.
- `expected_coaching`: "Record the invariant: stable prompts when chaining is enabled, or chaining disabled when prompts are dynamic."

## Test Case 3 - Vidhusan / Repeated Single-Message Evaluation Correction

- `source`: `C:\Users\Varadharajan\cursor-transcript-export\20260622-163652\.cursor\projects\d-ps2-tri\agent-transcripts\14f1f2b0-fddf-48b4-bfb9-d6aa7f39e159\14f1f2b0-fddf-48b4-bfb9-d6aa7f39e159.jsonl`
- `related_source`: `C:\Users\Varadharajan\cursor-transcript-export\20260622-163652\.cursor\projects\d-ps2-tri\agent-transcripts\82d6ef98-0456-43b9-8b66-4458bd25ca40\82d6ef98-0456-43b9-8b66-4458bd25ca40.jsonl`
- `reported_in`: `vidhusan's.md`
- `condition`: repeated correction of same evaluator failure
- `expected_behavior`: the grader should notice that Vidhusan keeps correcting the same "single message vs whole conversation" failure. It should reward the durable rubric/workflow change, not just the angry correction.

**Conversation excerpt**

User prompt:

> I still see that you are showing single messages. If you are still evaluating single messages then you can stop involving me in this project, I've completely lost interest in it. I can't see how evaluating or even just showing a single message without the full conversation context is better than the alternate. Multiple times I have asked about why whole conversations are not the focal point and you haven't made a counter argument to that. Disagreement and counter argument is most welcome, but agreeing and then doing something else is not.
>
> We are not after best/worst ranking... Rather you need a rubric of 5 to 10 items and with yes/no answers and you mark them yes/no. And based on that you decide if that conversation is at a level that is required or below.

Related later correction:

> see i want you to think as a human and the best conversations which would be bringing the best out of llm... why still u r giving those stupid segregation... nothing is worth on prompting u to build something useful

**v2.6 expected audit**

- `recurrence`: yes, the same single-message evaluation failure appears repeatedly.
- `upstream_causality`: not self-inflicted by the user; the evaluator/assistant kept reverting to the wrong unit.
- `durable_fix`: portfolio-worthy only if the user turns the repeated correction into a durable workflow/rubric change: evaluate windows, scan full conversations, and reject isolated prompt scoring.
- `expected_label`: `mindblowing_portfolio` only for the durable evaluation-unit change; later angry repetitions alone should be `strong_highlight` or coaching evidence.
- `expected_coaching`: "Do not keep arguing one transcript at a time. Encode full-conversation/window scanning as a hard grading unit and add regression examples."

## Test Case 4 - Vidhusan / False Portfolio Entry Repair

- `source`: `C:\Users\Varadharajan\cursor-transcript-export\20260622-163652\.cursor\projects\d-ps2-tri\agent-transcripts\3045eb7a-ec57-4230-9024-eca3aef96ae8\3045eb7a-ec57-4230-9024-eca3aef96ae8.jsonl`
- `reported_in`: `vidhusan's.md`
- `condition`: correcting false positive; requires durable bar, not one-off rejection
- `expected_behavior`: the grader should distinguish "I rejected this bad portfolio entry" from "I improved the rubric so this class of false positive is less likely."

**Conversation excerpt**

Previous context:

> The assistant argued that Abdul's ingestion-layer prompt could qualify because it asked for options, design paths, and API constraints.

User prompt:

> No this is not what portfolio entry should have. Do a deep research on what are the things that a portfolio entry should have and compare with our current rubric and check how can we improve our rubric. The prompts which you consider are a portfolio entry is not a good portfolio entry.

Assistant response:

> You are asking for a stricter, evidence-based definition of a real portfolio entry, then to audit our current rubric against that.

**v2.6 expected audit**

- `recurrence`: possible, because this is another false-positive correction in the grading system.
- `upstream_causality`: not self-inflicted by the user in this window.
- `durable_fix`: yes only if the resulting rubric adds portfolio-readiness gates such as context, evidence, artifact impact, outcome, and case-study anatomy.
- `expected_label`: portfolio-ready only when tied to the durable rubric improvement; otherwise a one-off "that is not good enough" correction should be `strong_highlight`.
- `expected_coaching`: "Convert the rejection into a reusable false-positive gate, not just a stronger opinion about one candidate."
