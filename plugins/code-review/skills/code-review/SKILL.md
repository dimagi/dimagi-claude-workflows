---
name: code-review
description: This skill should be used when the user asks to review code, check a PR, audit a file or module, look at code quality, assess a codebase, or says things like "what do you think of this code", "review my changes", "look at this file", "check this PR", or "does this look right". Trigger on any request to evaluate, critique, or assess code — even casually phrased ones. Performs thorough, senior-engineer-quality code reviews that go beyond bug detection.
---

# Code Review Skill

Orchestrate a thorough code review by spawning **5 parallel specialist reviewers**, each deeply focused on one dimension, then synthesise their findings into a coherent, prioritised review.

---

## Step 1: Understand Scope and Context

Before spawning reviewers, establish:

- **What to review** — files, directory, PR diff, or pasted code
- **Language and framework** — infer from context; confirm if ambiguous
- **Purpose of the code** — what is it trying to do?
- **Review depth** — quick pass vs. deep dive? (default: thorough)

If the user just pastes code or says "review this", infer context and proceed immediately. Only ask if something critical is missing.

**Read the code first.** Use `Read` to read files and `Glob` to scan directory structure before spawning agents. Enough context is needed to give agents useful starting information and file paths.

---

## Step 2: Spawn Parallel Reviewer Agents

Create a temp working directory:
```
/tmp/code-review-{timestamp}/
```

**Before spawning agents**, resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path (it's available in your environment) and substitute it into the agent prompts below. Subagents don't have access to this variable.

Spawn **all 5 agents simultaneously** (in parallel, not sequentially). Each agent:
- Reads the same code (provide paths or content)
- Focuses on exactly one dimension
- Writes findings to its own JSON file in the working directory

Agents to spawn (see `${CLAUDE_PLUGIN_ROOT}/agents/` for full instructions for each):

| Agent file | Output file | Focus |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/agents/design-reviewer.md` | `design.json` | Architecture, separation of concerns, coupling, layering |
| `${CLAUDE_PLUGIN_ROOT}/agents/quality-reviewer.md` | `quality.json` | Clean code, naming, DRY, refactoring opportunities |
| `${CLAUDE_PLUGIN_ROOT}/agents/smells-reviewer.md` | `smells.json` | Code smells, hacks, workarounds, anti-patterns |
| `${CLAUDE_PLUGIN_ROOT}/agents/security-reviewer.md` | `security.json` | Vulnerabilities, input validation, auth, secrets, exposure |
| `${CLAUDE_PLUGIN_ROOT}/agents/maintainability-reviewer.md` | `maintainability.json` | Testability, error handling, dead code, documentation |

**Prompt to give each agent** (replace all bracketed values and `${CLAUDE_PLUGIN_ROOT}` with absolute paths before sending):

```
Read your reviewer instructions from [/absolute/path/to/agents/agent-file.md].

Also consult [/absolute/path/to/skills/code-review/references/language-notes.md]
for the relevant [language/framework] section — it contains idiomatic patterns,
common pitfalls, and framework conventions to check.

Then review the following code:
- Code location: [path(s) to files]
- Language/framework: [detected]
- Purpose: [brief description of what the code does]
- Output path: /tmp/code-review-{timestamp}/[output-file]

Focus only on your assigned dimension. Be thorough within your domain.
```

---

## Step 3: Wait and Collect Results

Once all agents complete, read all 5 JSON files from the working directory. Each contains an array of findings in a standard format (see agent files for schema).

---

## Step 4: Synthesise Findings

Before writing the review, process the collected findings:

**Deduplicate**: Multiple agents may flag the same issue from different angles (e.g., a god class flagged by both design and smells agents). Merge these into a single finding — don't list the same issue twice.

**Calibrate severity**: Review the severity each agent assigned and apply engineering judgment. If 3+ agents flag the same root cause, that's a strong signal it's major or critical.

**Find cross-cutting themes**: Look for a single root cause that explains multiple findings across different agents. Surface it as a design observation rather than listing all its symptoms separately.

**Assess the overall picture**: Is this code fundamentally healthy with some rough edges? Or is there a deeper structural problem?

---

## Step 5: Write the Review

Structure the final review as follows:

### Summary
2–4 sentences on the overall state of the code. Be honest and direct. Praise what's genuinely good.

### Findings
Grouped by severity (🔴 Critical → 🟠 Major → 🟡 Minor → 💡 Suggestion):

```
**[emoji] Title** (`path/to/file.py`, line X–Y)

What the problem is and why it matters — the actual consequence or risk.

*Suggestion:* What to do instead, with a brief code snippet if it genuinely helps.
```

Severity guide:
- 🔴 **Critical** — Security vulnerability, data loss risk, correctness bug. Must fix.
- 🟠 **Major** — Significant design problem or dangerous pattern that causes pain at scale. Should fix.
- 🟡 **Minor** — DRY violation, naming issue, or improvement that meaningfully improves clarity. Worth fixing.
- 💡 **Suggestion** — Refactoring opportunity or nice-to-have worth considering.

### 🔵 Design Observations
Higher-level architectural concerns that span multiple findings — the "core issue" narrative.

### ✅ What's Working Well
2–4 things done well. Anchors the review and tells the author what to preserve.

---

## Tone and Style

- Write like a respected senior colleague, not a linter
- Explain the *why* behind every non-trivial finding
- Avoid piling on for the same root issue — note the pattern once
- Adapt depth to context: a 20-line utility vs. a 500-line module warrant different depth

---

## Step 6: Cleanup

Remove the temp working directory once the review is delivered:
```bash
rm -rf /tmp/code-review-{timestamp}/
```

---

## After the Review

- Ask if the author wants to dig deeper on any specific finding
- Offer to sketch out a refactored structure for major design issues
- Offer to pair on the fix for any specific section

---

## Fallback: No Sub-Agents Available

If running in an environment without sub-agent support (e.g., claude.ai web), review the code by working through each dimension in sequence using the agent files as checklists, and consult `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/language-notes.md` for language-specific guidance. The output format is identical.

---

## Additional Resources

- **`${CLAUDE_PLUGIN_ROOT}/agents/`** — Full reviewer instructions and JSON output schema for each specialist dimension
- **`${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/language-notes.md`** — Language-specific idioms, common pitfalls, and framework conventions (Python, Django, JS/TS, React, Node, Go, Java/Kotlin, SQL)
