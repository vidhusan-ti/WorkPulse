---
name: ipd
description: Drafts Important Product Decision (IPD) documents from rough product notes, options, tradeoffs, and decisions. Use when the user asks to create, structure, rewrite, or improve an IPD, product decision record, decision template, or option reasoning.
disable-model-invocation: true
---

# Important Product Decision

Create concise IPD documents that make the product owner's judgment visible: why the decision matters, what attributes define a qualifying solution, which option is selected, and the deciding reasoning.

## When to run

Use this skill when the user asks to:
- create an Important Product Decision or IPD
- compare product options and select one
- convert rough notes into a decision record
- improve the reasoning in a product decision document

If the user has not provided enough context, ask for the problem, target user, candidate options, decision owner, must-have attributes, and any known constraints.

## Source template

Use this template structure. Preserve the section order.

```markdown
Important Product Decision (IPD) Template


## WIP
<!-- Remove this when done -->
## Problem to solve
<!-- Give some context here to explain why the decision has to be made. It should be possible to trace this decision back to a user story or business problem -->

## Important attributes of a qualifying solution
<!-- The things you care about and the ones you don't. This is a very important section and your main contribution, because the remainaing sections are busy work and can be done by LLMs or other people. Here you write things that only you (the Product owner) can make the decisions about, because you have the context.

## Options

### Option 1
<!-- Short (<10 words) summary of the option]: [How the option would feel to the user. Paint a picture. How would the user interact with the system if this option was picked. -->
<!-- **Mark the selected option in bold** -->

### Option 2

### Option 3

## Reasoning
<!-- Avoid works like, simple, complex, easy, and difficult and explain why it is simpler/easier -->
<!-- Don't list pros and cons, instead highlight one or two deciding factor/s -->
```

## Drafting workflow

1. Identify the business or user problem that forced the decision.
2. Extract the qualifying attributes. Treat this as the most important section.
3. Rewrite each option as a short name plus a user-facing description of how it would feel in practice.
4. Mark the selected option in bold.
5. Write reasoning around one or two deciding factors, not a pros/cons table.
6. Remove `## WIP` when the user asks for a final IPD or the decision is clearly complete.

## Writing guidance

- In `Problem to solve`, make the decision traceable to a user story, operational pain, business risk, or product opportunity.
- In `Important attributes`, include the things the product owner cares about and what they explicitly do not care about.
- In `Options`, keep each option label under 10 words when possible, then paint the user's experience if that option is chosen.
- In `Reasoning`, explain why the selected option wins using concrete causes, constraints, reversibility, operational impact, user experience, or future migration paths.
- Avoid words like `simple`, `complex`, `easy`, and `difficult` unless followed by the concrete reason.
- Do not list pros and cons. Highlight the deciding factor or factors.
- Use confident product language. Do not over-explain obvious mechanics.

## Output format

Return only the IPD unless the user asks for commentary.

```markdown
# IPD. [Decision title]

## WIP
<!-- Remove this when done -->

## Problem to solve
[Context that makes the decision necessary.]

## Important attributes of a qualifying solution
[Product-owner criteria, constraints, non-goals, and success attributes.]

## Options

### **[Selected option name]**
[Short user-facing picture of how this option works in practice.]

### [Option name]
[Short user-facing picture of how this option works in practice.]

### [Option name]
[Short user-facing picture of how this option works in practice.]

## Reasoning
[One to three paragraphs focused on the deciding factor or factors.]
```

## Style reference

Use the example's structure as a guide:
- Title names the decision and selected direction.
- Problem is a direct question or concrete decision need.
- Options are enumerated and the selected option is clearly marked.
- Reasoning starts from system requirements, then explains why the selected option fits.
- Rejected options are addressed through the deciding factors, not balanced pros/cons.
- Migration or reversibility is mentioned when it reduces decision risk.

## Quality bar

Before finalizing, verify:
- The problem explains why the decision has to be made now.
- The selected option is bold.
- The qualifying attributes could only come from someone with product context.
- The reasoning avoids generic labels like `easy` and explains the actual mechanism.
- The document makes a decision instead of merely comparing options.
