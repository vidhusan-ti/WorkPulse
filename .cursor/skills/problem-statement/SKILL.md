---
name: problem-statement
description: Generates polished problem statements from rough ideas, product concepts, or raw notes. Use when the user asks to create, rewrite, structure, or improve a problem statement in a narrative style similar to the provided insight/coaching and legal-document examples.
disable-model-invocation: true
---

# Problem Statement Generator

Generate a clear, persuasive problem statement from a rough problem idea. Match the structure and tone of the user's examples: start from a broader belief or recurring situation, explain the pain and fragmentation, show the consequence, then state the opportunity if the problem were solved.

## When to run

Use this skill when the user asks for a problem statement, gives a rough product/problem idea, or asks to rewrite notes into a problem-statement format.

If the user gives too little context, ask for the domain, target users, current workflow, pain points, and desired outcome.

## Style to match

Use a concise narrative style:
- Start with the broader truth, belief, or recurring context behind the problem.
- Describe what people currently do and why it is painful.
- Name where information, effort, or decisions are fragmented.
- Explain the consequence: slower work, repeated effort, missed risk, poor quality, weak learning, or lower confidence.
- End with the benefit if the problem were solved.

Avoid solution design unless the user explicitly asks for it. The output should make the problem feel important before proposing what to build.

## Reference templates

The examples below are style references. Do not copy them unless the user's problem is the same.

### Template 1

```text
We believe that people bring value by providing insight, not information. Gathering information can now be done by AI tools faster and better than any human. Therefore value comes from:
- asking the right questions at the right time
- providing insight from context they, have to enable AI or other people to make the right decisions with a task
- wisdom and common sense to spot when they need to cross question or ask for details to mitigate risks

Then there are more basic practices like
- articulating questions and ideas properly so as to make it easy for the other person to understand and respond
- not offloading work when talking to other people, but doing homework, having a recommendation attitude and seeking opinions but not permission.
- Bias for action and refusal to be blocked or stuck on other people.

However, people need feedback to learn and this is no exception. Without feedback people learn slowly and the hard way. If there was a tool that provided timely feedback and potentially coaching on the above, we would all benefit.
```

### Template 2

```text
Legal teams routinely spend a lot of time reconstructing context for incoming requests.
Relevant information is often scattered across emails, Jira tickets, intake systems, and previously submitted documents.

As a result, legal professionals repeatedly search for prior agreements, re-evaluate issues that were addressed previously, and try to manually locate relevant clauses across multiple systems.
This fragmentation leads to slower response times, and increased risk of overlooking relevant historical decisions.
If legal teams could quickly find relevant documents, past requests, and specific clauses using simple natural-language queries, legal teams could spend less time searching.
```

## Generation workflow

Follow this process:

1. Identify the target user or team.
2. Identify the recurring situation they face.
3. Identify where context, information, work, or decision-making breaks down.
4. Identify the repeated manual behavior caused by that breakdown.
5. Identify the business/user consequence.
6. End with the outcome that would be possible if the problem were solved.

## Output format

Return only the problem statement unless the user asks for analysis.

Use this structure by default:

```text
[Target users/team] often [recurring situation or responsibility].
[Important context/information] is often [fragmented, missing, delayed, hard to interpret, or scattered across systems/people].

As a result, [target users/team] repeatedly [manual/redundant behavior], [decision/risk behavior], and [coordination/search behavior].
This leads to [primary consequence], [secondary consequence], and [risk/cost].
If [target users/team] could [desired capability] using [simple/natural workflow], they could [higher-value outcome].
```

## Quality bar

Before finalizing, check:
- The statement is about the problem, not the feature list.
- The target user is clear.
- The current pain is concrete and repeated.
- The consequence explains why the problem matters.
- The final sentence expresses the opportunity without over-specifying the implementation.
- The tone is direct, senior, and product-oriented.

## Optional additions

If useful, include these only when the user asks:
- `Inputs`
- `Outputs`
- `Scope`
- `Target audience`
- `Problem breakdown`
- `Assumptions / open questions`
