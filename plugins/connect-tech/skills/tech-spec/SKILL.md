---
name: tech-spec
description: Use when a technical spec, design doc, or PRD needs creating, reviewing, auditing, condensing, or restructuring — the user supplies a spec file path, PR link, Jira ticket, or pasted spec text and asks whether it is complete, whether it covers everything, to tighten or cut it down, to check it against the standard outline, or to rewrite it.
---

# Create and Review technical spec

## Overview

A spec is judged by the questions it answers and how clear it is stated, not by how much it says. This skill
audits a spec against a fixed question bank, closes the gaps, and rewrites it to a
standard outline using plain and easy language. This skill can also be used to create a spec from scratch.

If the user provided a spec, read the spec and make sure you have a good understanding of what the spec proposes. 
1. If there are any missing pieces to the spec so that the spec cannot reliably be generated with the given outline, go to Step 1.
2. If the spec is very clear on what the problem + solution is and there are no gaps in the proposal, go to Step 2 directly.

## Step 1: Creating or editing a spec

This step should be used whenever the user does not have a spec, or have provided an incomplete spec.

### Process

1. **Identify the problem.** Ask the user to state the problem as clearly as possible, or read it from a file/context they provide.
2. **Identify the solution.** Ask the user to state a summary of the solution they are thinking about, or read it from the provided file/context.
3. **Map the decision tree.** Identify all open questions, assumptions, and decision branches.
4. **Walk each branch one question at a time.** Ask a single focused question, wait for the answer, then move to the next. Never batch multiple questions.
5. **Track dependencies.** If a decision depends on an earlier unresolved one, resolve the dependency first.
6. **Challenge weak answers.** If the user's answer is vague, contradictory, or hand-wavy, push back with a specific follow-up.
7. **Maintain a design document.** Record every question and its resolution in the design doc. Update it as you go so the user can see the accumulated decisions. Follow the code names rule below from the start, so the names don't have to be stripped out later.

### When to stop

Stop when every branch of the decision tree has a concrete resolution and the user confirms the design document reflects the plan, after which you will hand it off to the
next step below for processing the spec.

## Step 2: Processing an existing spec

This step should be used when an existing spec is complete and clear on
1. what the problem is that needs solving
2. how it's going to solve it
3. why the solution is effective

The output of this step is a document having the outline defined in spec-outline.md.

### Audience and language policy
The audience is software developers, so technical terms can be used, but the document's language should be consice, explaining concepts in simple English terms that any reader not part of the creation of the document can easily understand, in other words without any mannered prose. It's **VERY IMPORTANT** to consider the external audience, so refrain from using any terms that might only be meaningful to somebody like the author who was part of the document's creation - rather explode the terms and be clear on what you mean.

The code names rule below applies here, and the identifier check at the end of this step is mandatory.

### Style rules

- Use bullets for any list of related points, not a paragraph that counts them ("Four properties of these rules are…").
- Answer the "why" questions a reviewer would actually ask about the design. Skip the why for small implementation choices.
- Leave out any section or subsection that would be empty. Don't write a heading followed by "None". The only exception is the "At a glance" table, where a "None" row shows the area was checked.
- Keep design and implementation apart: explain behaviour and key decisions in plain language, and use code names only where the code names rule allows.

### Identifier check (mandatory, before handing over the spec)

Don't hand over the spec until you've done this pass:

1. Go through the draft from top to bottom and list every code name in the order it first appears: classes, models, fields, functions, views, tasks, settings, flags, URLs and file paths.
2. For each name, check:
   - **Is it needed?** It's needed if the spec introduces it, or if a reviewer needs it to find the code. If it isn't needed, rewrite the sentence in plain language and remove the name.
   - **Is it explained where it first appears?** That means a plain-English phrase next to it, a link to the code, or a table row with a Purpose or Notes column. If not, add one.
   - **Is it used before that point?** If so, move the explanation up or rewrite the earlier sentence without the name.
3. Check that the Overview contains no code names at all.
4. Fix the draft, then hand it over. Tell the user in one line how many names you removed or explained.

## Code names rule

This applies to everything this skill writes, including the design document kept during Step 1.

Code names (classes, functions, fields, settings, flags) are terms only the author knows. A reviewer who hasn't read the code can't tell what `ConfigurationSession` or `_attempt_send` is.

- **Describe behaviour first, name code only when the name helps.** Name something when the spec introduces it (a new model, route, setting or task) or when a reviewer will need to find it in the code. Leave out internal helpers and private functions. "Calls to the vendor give up after 10 seconds" needs no function name.
- **Explain every name the first time it appears**, with a short plain-English phrase or a link to the code, e.g. "`ConfigurationSession`, the record that tracks one user's in-progress setup". After that the bare name is fine. A table row with a Purpose or Notes column counts as the introduction.
- **Never use a name before it's introduced.** If an earlier section would need a name that's defined later, rewrite that sentence without it or define it there.

| Instead of | Write |
|---|---|
| "`send_session_otp` calls `_attempt_send`, which retries on `VendorTimeout`." | "Sending the one-time code retries when the SMS vendor doesn't answer in time." |
| "`ConfigurationSession.rank` is copied to the log row." | Leave it out. This is an implementation detail, not a design point. |
| "The new `ThingLimitMixin` enforces the cap." (first mention, nothing to explain it) | "A view mixin, `ThingLimitMixin`, stops users creating more things than their opportunity allows." |
