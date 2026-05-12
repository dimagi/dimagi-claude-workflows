---
description: Thorough code review including a USS Tech impact specialist — runs code-review's 5 standard reviewers in parallel with a 6th USS-specific reviewer, then renders a two-block synthesis (standard + USS section).
---

# USS Review

Orchestrate a thorough code review by spawning **6 parallel specialist reviewers** — code-review's standard 5 plus the USS impact specialist — then synthesise findings into a two-block output: the standard code-review synthesis, followed by a USS section with audience-bucketed user-facing changes.

This command depends on the `code-review` plugin being installed (it reuses code-review's 5 agent files via sibling-path lookup).

---

## Step 0: Preflight — verify code-review is installed

Resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path. The 5 code-review agent files are expected at:

```
${CLAUDE_PLUGIN_ROOT}/../code-review/agents/design-reviewer.md
${CLAUDE_PLUGIN_ROOT}/../code-review/agents/quality-reviewer.md
${CLAUDE_PLUGIN_ROOT}/../code-review/agents/smells-reviewer.md
${CLAUDE_PLUGIN_ROOT}/../code-review/agents/security-reviewer.md
${CLAUDE_PLUGIN_ROOT}/../code-review/agents/maintainability-reviewer.md
```

Verify each file exists. If any are missing, print:

> The `/uss-review` command depends on the `code-review` plugin, which does not appear to be installed. Install it via `/plugins` (add the `dimagi-claude-workflows` marketplace if needed) and retry.

Then exit without spawning any agents.

---

## Step 1: Understand scope and context

Before spawning reviewers, establish:

- **What to review** — files, directory, PR diff, or pasted code
- **Language and framework** — infer from context; confirm if ambiguous
- **Purpose of the code** — what is it trying to do?
- **Review depth** — quick pass vs. deep dive? (default: thorough)

If the user just pastes code or says "uss-review this", infer context and proceed immediately. Only ask if something critical is missing.

**Read the code first.** Use `Read` to read files and `Glob` to scan directory structure before spawning agents.

---

## Step 2: Spawn 6 parallel reviewer agents

Create a temp working directory:

```
/tmp/uss-review-{timestamp}/
```

Spawn **all 6 agents simultaneously** (in parallel, not sequentially). Each agent:
- Reads the same code (provide paths or content)
- Focuses on exactly one dimension
- Writes findings to its own JSON file in the working directory

| Agent file | Output file | Focus |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/../code-review/agents/design-reviewer.md` | `design.json` | Architecture, separation of concerns, coupling, layering |
| `${CLAUDE_PLUGIN_ROOT}/../code-review/agents/quality-reviewer.md` | `quality.json` | Clean code, naming, DRY, refactoring opportunities |
| `${CLAUDE_PLUGIN_ROOT}/../code-review/agents/smells-reviewer.md` | `smells.json` | Code smells, hacks, workarounds, anti-patterns |
| `${CLAUDE_PLUGIN_ROOT}/../code-review/agents/security-reviewer.md` | `security.json` | Vulnerabilities, input validation, auth, secrets, exposure |
| `${CLAUDE_PLUGIN_ROOT}/../code-review/agents/maintainability-reviewer.md` | `maintainability.json` | Testability, error handling, dead code, documentation |
| `${CLAUDE_PLUGIN_ROOT}/agents/uss-reviewer.md` | `uss.json` | USS Tech audience inventory, gate correctness, blast radius |

**Prompt to give each agent** (replace bracketed values with absolute paths and concrete values before sending):

```
Read your reviewer instructions from [/absolute/path/to/agent-file.md].

Also consult [/absolute/path/to/code-review/skills/code-review/references/language-notes.md]
for the relevant [language/framework] section — it contains idiomatic patterns,
common pitfalls, and framework conventions to check.

Then review the following code:
- Code location: [path(s) to files]
- Language/framework: [detected]
- Purpose: [brief description of what the code does]
- Output path: /tmp/uss-review-{timestamp}/[output-file]

Focus only on your assigned dimension. Be thorough within your domain.
```

The USS reviewer does **not** need to consult `language-notes.md` — its focus is platform-impact, not language idioms. Omit that line from its prompt.

---

## Step 3: Wait and collect results

Once all 6 agents complete, read all 6 JSON files from the working directory.

---

## Step 4: Synthesise findings

Process the standard 5 results the same way code-review does today:

**Deduplicate**: Multiple agents may flag the same issue from different angles. Merge into a single finding.

**Calibrate severity**: If 3+ agents flag the same root cause, that's a strong signal it's major or critical.

**Find cross-cutting themes**: Look for a single root cause that explains multiple findings.

**Assess the overall picture**: Is this code fundamentally healthy with some rough edges, or is there a deeper structural problem?

The USS reviewer's findings are kept **separate** from the standard 5 — they are not merged into the same triage table. The USS section renders independently.

---

## Step 5a: Write Block 1 — standard code-review triage

Output the standard code-review triage format (same as the `code-review` skill produces today):

### Summary
2–4 sentences on the overall state of the code. Be honest and direct. Praise what's genuinely good.

### Findings

Compact numbered table — one row per finding, no detail yet:

| #  | Sev | Finding | Location |
|----|-----|---------|----------|
| 1  | 🔴  | [title] | [file:line] |
| 2  | 🟠  | [title] | [file:line] |

Severity key: 🔴 Critical · 🟠 Major · 🟡 Minor · 💡 Suggestion

Order by severity, number sequentially starting at 1.

### 🔵 Design Observations
Higher-level architectural concerns spanning multiple findings.

### ✅ What's Working Well
2–4 things done well.

---

## Step 5b: Write Block 2 — USS section

After Block 1, output a `---` separator and then:

```
## USS Impact

### Summary
[2–3 sentences from uss.json summary field]

### USS Findings
| #  | Sev | Finding | Location |
|----|-----|---------|----------|
| U1 | 🔴  | [title] | [file:line] |
| U2 | 🟠  | [title] | [file:line] |

### User-Facing Changes by Audience

**Ungated (affects all CommCare users)**
- [change 1]
- [change 2]

**Behind flag `FLAG_NAME`**
- [change]

**Subscription `Pro+`**
- [change]

**Project setting `setting_name`**
- [change]
```

**Numbering**: USS findings use `U` prefix (`U1`, `U2`, ...). Order by severity, number sequentially starting at `U1`.

**Audience ordering** in `User-Facing Changes by Audience`:
1. `ungated` bucket first (highest-leverage information — widest impact)
2. `flag:*` buckets next
3. `subscription:*` buckets next
4. `setting:*` buckets last

Within each bucket, list changes in the order they appear in the USS reviewer's JSON output.

**Omit empty buckets entirely** — do not render a heading for an audience with zero changes.

If the USS reviewer produced no findings at all, render the section with just the Summary and the User-Facing Changes (omit the findings table). If there are no user-facing changes either, render only the Summary.

---

## Step 5c: Gate on user selection

After outputting both blocks, use `AskUserQuestion` to ask:

> "Which findings do you want to expand? Enter numbers (e.g. `1,3` or `U1,U2`), a range (`1-4`, `U1-U3`), `all`, or `fix 2,U1` to implement directly. Or just ask about any finding."

---

## Step 5d: Expand and fix loop

Parse the user's response from Step 5c. The parser recognises both the main numbering (`1`, `2`, ...) and the USS prefix (`U1`, `U2`, ...):

| Input pattern | Action |
|---------------|--------|
| `1,3,5` | Expand main findings 1, 3, 5 |
| `U1,U3` | Expand USS findings U1, U3 |
| `1-4` | Expand main findings 1 through 4 |
| `U1-U3` | Expand USS findings U1 through U3 |
| `1,U2` | Mixed list — expand main #1 and USS #2 |
| `all` | Expand all findings in both tables |
| `fix 2,U1` | Expand + implement main #2 and USS #1 |
| `fix all` | Expand + implement all findings |
| Natural language (e.g. "tell me more about the SQL issue") | Map to the closest matching finding by title/topic; if no confident match, ask the user to clarify which finding they mean |

**Expanding a finding** means writing the full detail block:

```
**[emoji] Title** (`path/to/file.py`, line X–Y)

What the problem is and why it matters — the actual consequence or risk.

*Suggestion:* What to do instead, with a brief code snippet if it genuinely helps.
```

Use the severity guide from Step 5a.

**Implementing a finding** (`fix N` or `fix UN`): after expanding, make the code change immediately. Summarise what was changed in 1–2 sentences.

**After expanding/fixing**, use `AskUserQuestion` to ask:

> "Anything else to address? Pick more numbers (`1`, `U2`, ...), ask about a finding, or say 'done'."

If the user pushes back on a finding ("I disagree with U2"), engage with their reasoning directly — they may have context that changes the assessment. This is a conversation, not a report.

Exit the loop when the user says "done" or when their response cannot be interpreted as a finding selection, fix request, or pushback.

---

## Step 6: Cleanup

Remove the temp working directory:
```bash
rm -rf /tmp/uss-review-{timestamp}/
```

---

## Tone and style

- Write like a respected senior colleague, not a linter
- Explain the *why* behind every non-trivial finding
- Avoid piling on for the same root issue — note the pattern once
- Adapt depth to context: a 20-line utility vs. a 500-line module warrant different depth
- In the USS section, frame findings as confirmation prompts rather than compliance failures. Ungated work is not, by itself, a problem.

---

## Fallback: no sub-agents available

If running in an environment without sub-agent support, review the code by working through each dimension in sequence using the 6 agent files as checklists. The output format is identical (two blocks).
