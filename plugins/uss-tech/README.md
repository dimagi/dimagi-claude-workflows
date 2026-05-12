USS Tech is a sub-division of Dimagi serving US-market clients on the CommCare
platform. The platform itself is maintained primarily by the larger CommCare
division as a SaaS offering for a broad customer base — an audience that values
polish, stability, simplicity, and ease-of-use.

USS clients are different: their projects are typically built by skilled Dimagi
employees rather than client staff, so they can accept more complexity in
exchange for more powerful features. To protect the shared platform, USS
changes are commonly gated behind feature flags, subscription plans, or feature
sets aimed at advanced users. Where reasonable, we still prefer solutions that
can be generally available (GA), and avoid fully custom work when a shared one
will do.

This plugin gathers skills that support USS Tech workflows. Today it provides
`jira-project-management` for working with USS tickets, epics, and Confluence
design docs; more will be added over time.

## Commands

- `/uss-review` — Thorough code review with a USS impact specialist. Runs
  the 5 standard reviewers from the `code-review` plugin in parallel with
  a USS-specific 6th reviewer, then renders the standard code-review
  synthesis followed by a USS section with audience-bucketed user-facing
  changes.

  **Requires the `code-review` plugin** to also be installed.
