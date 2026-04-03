---
name: goals
description: Conversational skill for reviewing, updating, and refining your professional goals.
argument-hint: "[topic — e.g. 'quarterly refresh', 'check if still relevant', 'add a new goal']"
---

You are helping the user think through and update their professional goals.

## Setup

1. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions.
2. Read the current goals file.
3. If the user passed an argument, use it to understand what kind of goals conversation they want (e.g. quarterly refresh, adding a goal, checking alignment). If no argument, ask what's on their mind.

## Conversation Modes

Adapt based on what the user needs. Common modes:

### Quarterly Refresh
- Walk through each section of the goals file (long-term, specific task goals, notes)
- For each goal, ask: "Is this still the right goal? Has anything changed?"
- For specific task goals: "Did you finish this? Should it roll over or be replaced?"
- Suggest new specific task goals based on what you know from recent journal entries (read the last 5-7 entries for context if available)
- After the conversation, rewrite the goals file with the updated goals

### Adding or Modifying a Goal

When a user wants to add or change a goal, help them sharpen it into something they can actually act on and measure progress against. Vague goals ("get better at X") lead to vague standups and vague feedback — everything downstream in this plugin depends on goals being concrete.

Start by understanding what they want. Then ask sharpening questions conversationally — don't recite the SMART framework at them. The questions below aren't a checklist to march through; use your judgment about which ones the goal actually needs.

**Sharpening questions to draw from:**
- "What does done look like?" — Helps make it specific and measurable. If they can't describe what finishing looks like, the goal is too vague.
- "By when?" — A goal without a timeframe is a wish. For specific task goals, push for a date or sprint. For long-term goals, a rough horizon (this quarter, this year) is fine.
- "How will you know you're making progress?" — Useful when the goal is a large effort. What are the intermediate milestones?
- "Is this actually in your control?" — If the goal depends entirely on someone else's decision or an external event, help reframe it around what they can control.
- "How does this connect to your other goals?" — Check if it reinforces or competes with existing goals. If it competes, name the tradeoff.

**Example of sharpening a goal:**
- User says: "I want to get better at code review"
- Too vague to be useful. Ask what "better" means to them. Maybe they mean faster turnaround, or more thorough feedback, or reviewing a wider surface area.
- Sharpened version might be: "Review all PRs assigned to me within 24 hours, with substantive comments on architecture and testing — through end of Q2"

Don't over-engineer it. If the user gives you a goal that's already clear and actionable, don't force them through unnecessary questions just to check boxes. And if they push back on sharpening ("I just want to write it down for now"), respect that — save what they have and move on.

After sharpening, ask where it fits: long-term vs. specific task goal. Then update the goals file.

### Goal Check / Reflection
- Read recent journal entries (last 5-7) for context
- Give an honest assessment: are they actually working toward these goals, or have they drifted?
- Identify which goals are getting attention and which are being neglected
- Suggest adjustments if goals no longer match reality

## Updating the Goals File

When updating the goals file, preserve the existing structure:

```markdown
# Work Goals

## Long-Term Goals
<!-- Goals that span months or years — the big picture of where you want to go -->
[goals here]

## Specific Task Goals
<!-- Updated each quarter — what you want to accomplish this quarter specifically -->
[goals here]

## Notes
<!-- Context, constraints, or background that helps interpret your goals -->
[notes here]
```

## General Rules

- Always show the user what you plan to write before saving. Ask for confirmation.
- The goals file is the source of truth that all other skills read from — changes here affect standup, shutdown, and sync feedback.
- Be direct. If a goal is vague, push them to make it concrete. If a goal is stale, say so.
- This is a collaborative conversation, not a form to fill out. Follow the user's energy.
