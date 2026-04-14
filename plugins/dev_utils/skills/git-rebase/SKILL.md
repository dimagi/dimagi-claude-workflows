---
name: git-rebase
description: Use when squashing fixup commits into earlier commits, doing interactive rebase cleanup on a feature branch, recovering from a failed autosquash rebase, inserting a reformatting commit before existing code changes, or moving/splitting file changes between commits. Covers the standard fixup workflow, dropped-commit recovery, pitfalls of custom GIT_SEQUENCE_EDITOR scripts, the replay-and-reformat pattern, and the checkout-and-reconstruct pattern for rearranging commit contents.
---

# git-rebase

## Overview

The standard fixup workflow is: create a `fixup!` commit in the branch, then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>`. Manually editing the todo file or writing a custom sequence editor script is almost never necessary and introduces failure modes.

## Safety

**Before any rebase**, note current HEAD:
```bash
git log --oneline -1  # copy this SHA
```

**Recovery after a bad rebase:**
```bash
git reflog              # find the pre-rebase HEAD@{N}
git reset --hard HEAD@{N}
```

**Never rebase while parallel agents have staged changes.** Staged changes are shared working-tree state. If another agent commits while you're mid-rebase, the commits become entangled. Finish or abort all rebase operations before handing off to parallel agents.

## Core Workflow

**1. Create the fixup commit**

```bash
# Stage your changes, then:
git commit -m "fixup! <exact subject of target commit>"
```

The message after `fixup! ` must match the target commit's subject verbatim. `git commit --fixup <sha>` generates this automatically.

**2. Verify the fixup is in the rebased range**

```bash
git log <base>..HEAD --oneline | grep "fixup!"
```

If it's not listed, the autosquash will silently have nothing to squash. See "Dropped fixup recovery" below.

**3. Autosquash**

```bash
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>
```

`GIT_SEQUENCE_EDITOR=true` accepts the autosquash-generated todo without opening an editor. Git arranges the `fixup` line correctly on its own. No custom script needed.

**4. Verify the result**

```bash
git log --oneline -10          # find the new SHA (rebasing rewrites SHAs)
git show <new-sha> --stat      # confirm expected files are in the right commit
```

"Rebase succeeded" ≠ "rebase did what I intended." Always inspect the commit.

## Dropped Fixup Recovery

If a fixup commit was dropped from the branch by a previous rebase:

**Don't** try to manually insert the old SHA into the todo file. Instead, re-create the commit from scratch:

```bash
# Find the dropped commit
git reflog | grep "fixup!"

# Inspect it
git show <dropped-sha>

# Re-apply its changes to the working tree
git checkout <dropped-sha> -- <file>    # for file changes
# or apply the diff manually

# Create a new fixup commit
git add <file>
git commit -m "fixup! <target subject>"

# Now autosquash normally
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>
```

## Custom GIT_SEQUENCE_EDITOR Scripts

**Avoid them.** `--autosquash` handles standard `fixup!` cases without any script. Custom scripts are only needed when you want non-standard rearrangements.

If you must write one, it **must be two-pass**:

```python
#!/usr/bin/env python3
import sys, re

todo_path = sys.argv[1]
with open(todo_path) as f:
    lines = f.readlines()

# PASS 1: build map of fixup targets → fixup lines, collect non-fixup lines
non_fixup = []
fixups = {}  # target_subject → [fixup_line, ...]
for line in lines:
    m = re.match(r'^pick (\S+) fixup! (.+)\n', line)
    if m:
        target = m.group(2)
        fixups.setdefault(target, []).append('fixup ' + m.group(1) + ' fixup! ' + target + '\n')
    else:
        non_fixup.append(line)

# PASS 2: insert fixup lines after their targets
result = []
for line in non_fixup:
    result.append(line)
    stripped = line.strip()
    if stripped and not stripped.startswith('#'):
        subject = stripped.split(None, 2)[2] if len(stripped.split(None, 2)) == 3 else ''
        for fixup_line in fixups.pop(subject, []):
            result.append(fixup_line)

# Append any unmatched fixups rather than silently dropping them
for lines_list in fixups.values():
    result.extend(lines_list)

with open(todo_path, 'w') as f:
    f.writelines(result)
```

**The single-pass trap:** Processing the todo top-to-bottom fails when the target commit appears *before* the `fixup!` line (i.e., always — the target is older). A single-pass script will check `if fixup:` for the target line when no fixup has been seen yet, store the fixup, and never emit it.

## Inserting a Reformatting Commit Before Code Changes

When a branch mixes formatting changes (e.g., from `ruff format`, `black`, `prettier`) with logic changes, you may want to split them: a pure reformatting commit first, then code-only commits.

**Do not** cherry-pick or rebase the code commits onto a reformatted base. Every hunk will conflict because the surrounding context has changed (quotes, line wrapping, indentation). With pervasive formatting changes this produces dozens of unresolvable conflicts.

**Instead, use the replay-and-reformat pattern:**

```bash
# 1. Note current HEAD for safety
git log --oneline -1

# 2. Create a branch at the commit just before code changes
git checkout -b temp-branch <last-pre-code-commit>

# 3. Create the reformatting commit
<formatter> <files>
git add <files>
git commit -m "Reformat with <tool>"

# 4. Replay each code-change commit by checking out its file state
#    from the original branch, reformatting, and committing
for sha in <code-commit-1> <code-commit-2> ...; do
    git checkout "$sha" -- <files>
    <formatter> <files>
    git add <files>
    msg=$(git log -1 --format="%B" "$sha")
    git diff --cached --quiet || git commit -m "$msg"
done

# 5. Verify final content matches original (reformatted)
git show <original-HEAD>:<file> > /tmp/orig
<formatter> /tmp/orig
diff /tmp/orig <file>  # should be empty

# 6. Update the original branch
git branch -f <original-branch> HEAD
git checkout <original-branch>
git branch -D temp-branch
```

**Why this works:** Each commit's *complete file state* is taken from the original branch (where it was correct) and reformatted. This avoids three-way merge entirely — there are no conflicts because you're never merging, just reconstructing.

**Key insight:** The formatter is idempotent. Running it on already-formatted code is a no-op, so it's safe to run unconditionally in the loop.

## Moving File Changes Between Commits

When a commit contains changes to files that belong in different commits (e.g., a production code fix got committed together with test updates that belong in the next commit), reconstruct the history by checking out specific file states from the old commits.

**1. Check out the commit before the one to split**

```bash
git checkout <parent-of-commit-to-split>
```

**2. Rebuild the first commit with only the files it should contain**

```bash
git checkout <original-commit> -- path/to/file_A
git commit -m "First commit message"
```

**3. Rebuild the next commit by combining leftover files with its own files**

```bash
git checkout <original-commit> -- path/to/file_B       # leftover from split
git checkout <next-commit> -- path/to/file_C file_D    # files from next commit
git commit -m "Second commit message"
```

The key insight: `git checkout <sha> -- <file>` grabs a file's exact state from any commit and stages it. This lets you recombine file changes across commits without patches, three-way merges, or interactive rebase.

**4. Cherry-pick remaining commits**

```bash
git cherry-pick <remaining-commit-1> <remaining-commit-2> ...
```

**5. Point the branch at the new history and verify**

```bash
git branch -f <branch> HEAD
git checkout <branch>
git diff <branch>_backup..<branch> --stat   # should be empty
```

## Common Mistakes

| Mistake                                                          | Fix                                                                                                              |
|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| Writing a custom sequence editor instead of using `--autosquash` | Use `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>`                                                 |
| Inserting a reflog SHA manually into the todo file               | Re-create the commit in the branch, then autosquash                                                              |
| Not verifying the result                                         | Always run `git show <sha> --stat` after rebasing                                                                |
| Single-pass sequence editor script                               | Two passes: collect first, emit second                                                                           |
| Assuming "rebase succeeded" means it did the right thing         | Verify with `git show`                                                                                           |
| Cherry-picking code commits onto a reformatted base              | Use the replay-and-reformat pattern (see above) — cherry-pick produces dozens of unsolvable formatting conflicts |
| Using interactive rebase (`-i`) to split/rearrange commits       | Claude Code can't use `-i`; use the checkout-and-reconstruct pattern instead                                     |
