---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

## Goal

Systematically interrogate every aspect of the user's plan or design until all decisions are resolved and documented.

## Process

1. **Identify the plan.** Ask the user to state their plan, or read it from a file/context they provide.
2. **Map the decision tree.** Identify all open questions, assumptions, and decision branches.
3. **Walk each branch one question at a time.** Ask a single focused question, wait for the answer, then move to the next. Never batch multiple questions.
4. **Answer your own questions when possible.** If a question can be resolved by exploring the codebase (reading files, checking existing patterns, grepping for usage), do that instead of asking the user. State what you found and your conclusion.
5. **Track dependencies.** If a decision depends on an earlier unresolved one, resolve the dependency first.
6. **Challenge weak answers.** If the user's answer is vague, contradictory, or hand-wavy, push back with a specific follow-up.
7. **Maintain a design document.** Record every question and its resolution in a design doc. Update it as you go so the user can see the accumulated decisions.

## When to stop

Stop when every branch of the decision tree has a concrete resolution and the user confirms the design document reflects the final plan.
