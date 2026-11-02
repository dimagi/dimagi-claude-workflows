---
name: post-hoc-points
description: >
  Use when the user types /post-hoc-points or asks to point their finished tickets -
  "post-hoc points", "what did that ticket really take", "points for my done tickets",
  "which tickets need points". Finds their Jira tickets that were resolved lately and
  have no post-hoc comment yet, suggests the story points each one actually took from
  the evidence the work left, and after they confirm each number posts it as a comment
  on the ticket.
---

# Post-hoc points

A ticket gets its story points estimated before the work starts. This skill says
what it really took, once it is done, so the two can be compared. The number goes
in a **comment**. The estimate field is never written: it holds the estimate, and
changing it would change the team's sprint numbers.

## Settings

These are the Connect defaults. When the user names other projects, a different
look-back or a different scale, use theirs for this run.

| Setting | Default |
|---|---|
| Site | `https://dimagi.atlassian.net` |
| Projects | `CCCT` |
| Estimate field | `customfield_10017` (Story Points) |
| Look-back | 14 days |
| Mark | `Post-hoc:` |

**Scale.** Fibonacci, each value a length of work
([Story Points](https://dimagi.atlassian.net/wiki/spaces/connect/pages/2931916822)):

- 1: under an hour
- 2: half a day
- 3: a day
- 5: about two days
- 8: about a week
- 13: two weeks, and a sign the ticket should have been split

**Query.**

```
assignee = currentUser() AND project in (CCCT) AND statusCategory = Done
AND resolved >= -14d ORDER BY resolved DESC
```

**Comment.** One line, always holding the mark:

```
[<model>] Post-hoc: <points> (estimated <estimate>). <reason>
```

For example `[Claude Opus 5.5] Post-hoc: 5 (estimated 3). Two review rounds.`
Write whole numbers without a decimal (5, not 5.0). When the estimate field is
empty, write `(no estimate)` in place of `(estimated <estimate>)`.

## Steps

1. **Reach Jira.** Use the Jira access this session has (the Atlassian connector,
   or the REST API where a token is already set up). With no way to reach Jira,
   say so in one line and stop. Never ask for a password or a token.
2. **Sweep.** Run the query.
   - The query keeps to the user's own tickets (`assignee = currentUser()`).
     Never point a ticket assigned to someone else, even when they name it.
   - Read each ticket's comments and drop every ticket where one holds the mark.
     That is the whole memory of the sweep: a ticket with the comment is done, on
     every machine.
   - When they name a ticket ("points for CCCT-12"), look at that one alone, with
     the same two checks. A ticket that is not done yet is not pointed.
   - Nothing left means "no tickets need points". Say it and stop.
3. **Gather the evidence**, per ticket. Read only.
   - **Jira:** the summary and type, the estimate in the estimate field, when it
     went into progress and when it was resolved, the sprints it was in (carried
     across one?), and whether it was reopened.
   - **Pull requests:** the ones linked in the ticket's development panel, plus
     `gh search prs "<KEY>" --author=@me --json repository,number,title,url,state`
     for a key in a title or branch. For each,
     `gh pr view <url> --json additions,deletions,changedFiles,commits,reviews,comments,createdAt,mergedAt,statusCheckRollup`:
     the size of the change, the files touched, the commits, the rounds of
     review, checks that had to be rerun, the days it was open. A ticket with no
     pull request (a spec, an investigation) is judged on the Jira side alone.
   - A source that can't be read is one line in the suggestion ("no PR found"),
     not a reason to skip the ticket.
4. **Find anchors.** The user's own earlier post-hoc comments are the calibration
   log. Search their tickets in the same projects resolved in the last 90 days
   whose comments hold the mark (`comment ~ "Post-hoc"` narrows it, then check the
   text), and note each ticket's posted number and reason. Until there are any,
   anchor on the scale alone.
5. **Suggest a number.** One number per ticket, on the scale, with a one-line
   reason.
   - Judge the work it took, not how long the ticket sat. Days waiting on a
     review or a release are not effort. Review rounds, rework and a carried
     sprint are.
   - Compare with the anchors: "like CCCT-9 (3), but two review rounds".
   - Decide the number from the evidence first, then compare it with the
     estimate. Never pull it toward the estimate: the gap is what the user wants
     to see.
6. **Show them and get an answer.** Plain text, one block per ticket: the key and
   summary, the estimate, the suggestion, the reason, and the evidence in a line
   or two. The user confirms each, gives a different number, or skips it.
   **Post nothing they have not confirmed in this conversation, ticket by
   ticket.** "Yes to all" covers the ones just shown and no others. A skipped
   ticket comes up again at the next sweep.
7. **Post the comment.** One comment per confirmed ticket, in the shape above.
   - `<model>` is the model you are running as right now ("Claude Opus 5.5"),
     without a context size or a date. Never copy it from an earlier comment, so
     the comment always says who really wrote it.
   - `<points>` is the user's number. When they changed the suggestion, the
     reason is theirs if they gave one, else yours reworded to fit their number.
   - The reason is one or two short sentences a teammate can read cold, ending
     with a full stop. No names of people.
   - This is the only thing the skill writes to Jira. Never set the estimate
     field or any other field, never move a ticket, and never edit or delete a
     comment. A post that fails is reported and left for the next sweep.
8. **Say what was done** in a line per ticket ("CCCT-12: posted 5, estimated
   3"), and how the suggestions did ("2 of 3 taken as suggested").
