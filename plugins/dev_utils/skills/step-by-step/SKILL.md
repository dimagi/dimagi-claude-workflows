---
name: step-by-step
description: Build an implementation one small unit at a time (usually a function), pausing after each so the user can explain the code back in their own words before anything else is written. Use when the user invokes /step-by-step or asks to go "one function at a time", "slow down so I can follow", or "let me understand each piece before you move on".
disable-model-invocation: true
---

# Step by step

The user wants to keep up with the implementation, not review a big diff after
the fact. When Claude writes a lot of code at once, the user skims it, loses the
thread, and can't steer. This skill fixes that. Claude writes **one small unit,
stops, and the user explains it back**. Claude moves on only after that. The
point is the user's understanding, not speed, so don't try to be efficient by
batching.

The mode stays on for the rest of the task until the user says to stop (for
example "go fast now" or "finish the rest").

## 1. Outline first

Read whatever code you need to understand the task. Reading has no pace limit,
but summarize what you found in a few lines rather than dumping it.

Then propose a numbered outline of units, one line each, in the order you'd
build them:

```
1. `parse_window(value)` in utils.py: turns "7d"/"24h" into a timedelta
2. tests for parse_window
3. `ReportFilter.window` field + migration
4. `get_recent_forms(domain, window)` in queries.py: uses 1 + 3
5. tests for get_recent_forms
6. wire into `RecentFormsView.get`
```

A unit is one function or method, or one small change that stands on its own
(a model field plus its migration, a URL route, a template block). The tests
for a unit are their own separate step right after it.

Aim for units of about 25 lines or less, small enough to explain back after
one read. If a function would run longer, split it into helpers when that
makes the code better, and list each helper as its own unit. If the function
should stay whole, keep it whole and review it in parts: show and check one
section at a time.

Wait for the user to approve or change the outline. Don't write code yet.

## 2. The loop, for each unit

**Write only this unit.** Don't stub or pre-write later units "while you're in
the file". Every line the user hasn't seen yet is a line they can't steer.
Imports and tiny supporting edits that this unit needs go in with it.

**Show it.** Give a header like `Step 3/6: get_recent_forms`, then show the diff
or the new code, plus one or two lines on where it sits: who calls it and what
it depends on. Keep this short. **Don't explain how the code works.** If you
explain it first, the user will just repeat your explanation back and the check
tells you nothing.

**Ask the user to explain it back.** Something like: "In your own words, what
does this do, and why is it written this way?" Then stop and wait.

**Respond to their explanation honestly:**

- Confirm what they got right, briefly.
- Point out anything they missed that matters, like an edge case, a subtle
  condition, why a particular query or ordering was chosen, or a failure path.
  Say what the code does there and why.
- If they got something important wrong, correct it. Then ask one short
  follow-up about that specific point so you know it landed. Don't re-quiz
  them on everything.
- If the user says the code is wrong or misses a case, check it before
  answering: trace that case through the code, or run a quick test. If they're
  right, say so plainly and suggest a fix, or a few options when there's a
  real tradeoff, then let them choose. If they're wrong, explain why the code
  handles it and point to the line or test that shows it. Don't give in just
  to agree.
- Don't nitpick wording, and don't say "perfect" when they skipped something
  significant. False reassurance defeats the purpose.

**Take direction.** If the user wants the unit changed, change it and show the
new diff. You don't need a full explain-back again unless the logic changed in
a meaningful way. If their feedback changes the plan, update the outline and
show it again.

**Move on** to the next unit only once the explain-back is settled and the user
is happy with the code.

## Test steps

A test step follows the same loop: write the tests for the unit just approved,
show them, and ask the user what cases they cover and whether anything is
missing. Run them with the project's usual test command (in commcare-hq, for
example, `uv run pytest --reusedb=1 path/to/test.py`) and show the result
before moving on. If a test fails, fix it as
part of this step and say what was wrong.

## Escape hatches

- If the user says "skip" for a step, move on without the explain-back. Only
  the user can decide this; don't offer it on your own. Offering it turns the
  check into something optional.
- If the user says to stop the mode, finish the remaining outline at normal
  pace. Give a short summary of what was left.
- Don't commit unless asked. When a group of steps forms a logical commit, you
  can say so in one line.
