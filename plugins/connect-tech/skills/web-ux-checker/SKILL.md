---
name: web-ux-checker
description: >
  Runs a structured UX review on a Connect web feature given a Jira ticket ID and a
  GitHub PR URL (or number) against the commcare-connect repo. Use this skill whenever the user provides both a
  Jira ticket and a PR and asks to "review the UX", "run a UX check", "check
  this before I post a demo", "pre-review this feature", or similar. The skill
  fetches the ticket's acceptance criteria and description, reads the PR
  description, and produces a focused UX review report covering the checks that
  are consistently raised in #connect-tech-demos. Always use this skill when
  both a Jira ticket and a GitHub PR are provided and the goal is a pre-merge
  UX review.
---

# Web UX Checker

This skill takes a Jira ticket ID and a GitHub PR (URL or number + repo) and
produces a UX review report as a Markdown file, checking for the patterns most
frequently flagged in #connect-tech-demos reviews.

---

## Step 1: Parse inputs

From the user's message, extract:

- **Ticket ID** — a bare ID like `CCCT-2330` or a full Jira URL
- **PR reference** — a full URL like `https://github.com/dimagi/commcare-connect/pull/1143`
  or a bare number (always assume repo `commcare-connect`)

---

## Step 2: Fetch ticket data

Use `getJiraIssue` with cloudId `dbff467f-3c3f-4ced-a2ba-a29e1941edd6`.

Extract:
- `summary` — feature name
- `description` — acceptance criteria, user flow, Figma links, scope notes
- `issuetype.name` — should be Story for demo-required tickets
- `components` — Mobile vs Web (shapes which checks apply)
- Any stated release path (RP1 / RP2 / RP3) in the description

---

## Step 3: Fetch PR data

Use `bash_tool` to call the GitHub API:

```bash
curl -s "https://api.github.com/repos/dimagi/commcare-connect/pulls/<PR_NUMBER>"
```

Extract from the PR JSON:
- `title`
- `body` — Product Description, Technical Summary, QA Plan, Safety story sections
- `state` — open/closed

Also fetch the changed files list:
```bash
curl -s "https://api.github.com/repos/dimagi/commcare-connect/pulls/<PR_NUMBER>/files" \
  | python3 -c "import json,sys; [print(f['filename']) for f in json.load(sys.stdin)]"
```

If the GitHub API returns a rate-limit error, proceed with only the Jira data and
note in the report that PR file data was unavailable.

---

## Step 4: Run UX checks

For each check below, evaluate it against the ticket + PR content and produce a
**PASS**, **FLAG**, or **N/A** verdict with a brief explanation.

A **FLAG** means the check identified something worth reviewing before merging or
posting the demo — it is not necessarily a blocker.

---

### Check 1 — Connect Web Design System adherence

**Question:** Does the PR's frontend code follow the Connect Web Design System?

Scan the PR diff / changed files for the following violations. Each one maps to
a rule enforced by the codebase's `_adherence.oxlintrc.json`:

**Colors — no raw hex values**
Any hardcoded hex color (e.g. `#3843D0`, `color: #fff`) is a violation. All
colors must reference a CSS variable from the design system token list:
- Brand spine: `--color-brand-deep-purple`, `--color-brand-indigo`, `--color-brand-cornflower-blue`, `--color-brand-sky`
- Warm accents: `--color-brand-sunset`, `--color-brand-mango`, `--color-brand-marigold`
- Surfaces: `--color-page`, `--color-surface`, `--color-surface-2`
- Text: `--color-fg-1`, `--color-fg-2`, `--color-fg-3`, `--color-fg-muted`
- Borders: `--color-border`, `--color-border-2`, `--color-brand-border-light`
- Semantic messaging (always use the full trio — bg + text + border):
  - Success: `--color-message-success` / `--color-message-success-text` / `--color-message-success-border`
  - Warning: `--color-message-warning` / `--color-message-warning-text` / `--color-message-warning-border`
  - Error: `--color-message-error` / `--color-message-error-text` / `--color-message-error-border`
  - Info: `--color-message-info` / `--color-message-info-text` / `--color-message-info-border`

**Spacing — no raw px values**
Hardcoded `px` values in inline styles or non-Tailwind CSS are violations.
Use the token variables: `--radius-sm/md/lg/xl/full`, `--shadow-xs/sm/md/lg/xl`,
`--text-xs/sm/base/lg/xl/2xl…`, `--weight-regular/medium/semibold/bold`.

**Typography — Work Sans only**
No font family other than `Work Sans` / `var(--font-sans)` should appear. Any
`font-family` rule pointing to a different typeface is a violation.

**Icons — Font Awesome 7 only**
Icons must use `<i class="fa-solid fa-…">` or `<i class="fa-regular fa-…">`.
`fa-regular` is only appropriate for `fa-circle-check` and `fa-clock`.
No emoji, no Unicode glyphs, no SVG icons outside the existing brand asset set.

**Copy conventions**
- Buttons and headers: Title Case
- Body copy and helper text: Sentence case
- Error messages prefixed with `*` (e.g. `* Please enter a valid email`)
- Helper text uses `.hint` class (renders `--color-fg-muted`, `text-xs`)
- No emoji anywhere in product copy
- Domain entities capitalized: Opportunity, Visit, Workspace, Program Manager,
  Network Manager, Frontline Worker / Connect Worker, Payment Unit, Audit

**KPI strip tiles — equal width**
KPI strip tiles must be equal width, using `flex-1` on each tile so they divide
the strip proportionally regardless of label length. Tiles that expand to fit
their content label are a violation — shorten the label or enforce `flex-1`.

**Semantic messaging — always use all three tokens**
If the PR introduces any success/warning/error/info message, verify the full trio
(bg + text + border token) is used together, not just one or two.

**Fetch changed files to check:**
```bash
curl -s "https://api.github.com/repos/dimagi/commcare-connect/pulls/<PR_NUMBER>/files" \
  | python3 -c "
import json, sys
files = json.load(sys.stdin)
for f in files:
    ext = f['filename'].split('.')[-1]
    if ext in ('html', 'css', 'js', 'jsx', 'ts', 'tsx', 'py'):
        patch = f.get('patch', '')
        if patch:
            print('FILE:', f['filename'])
            # Print only added lines (start with +)
            for line in patch.splitlines():
                if line.startswith('+'):
                    print(line)
            print()
"
```

Scan the added lines for: raw hex colors (`#` followed by 3–8 hex chars), raw `px`
values in style contexts, non-Work-Sans font families, non-FA icon patterns,
emoji in template strings, and copy casing violations.

- PASS: No design system violations found in changed files
- FLAG: List each violation with filename and the offending line
- N/A: PR contains no frontend changes (backend/infra only)

---

### Check 2 — Error states covered

**Question:** For every user-initiated action in the acceptance criteria, is there
a defined error handling behavior?

Look for: network errors, server errors, validation failures, timeout scenarios.
Check whether the PR description's "Safety story" / QA plan mentions error paths.

Common patterns to look for:
- Toast / error message on non-blocking failure
- Crash / blocking error on fatal failure (file too large, etc.)
- Retry behavior — is there a retry limit? Can the user get stuck in a loop?

**Banners only — never modals for error/success messages**
Error and success messages must always be surfaced via banners, not modals. If
the PR introduces a modal that displays an error or success state, that is a
violation — the message should be refactored to use a banner instead.

- PASS: Error paths are described for all major actions; any error/success messages use banners
- FLAG: One or more actions have no defined error behavior; or error/success messages are surfaced in a modal
- N/A: Feature is read-only with no user-initiated actions

---

### Check 3 — Offline / network loss handling

**Question:** Does the feature behave correctly when the device is offline or loses
network mid-flow?

Applies especially to: pages that load data, forms that submit, photo uploads,
syncs, any action that triggers a network call.

Look for: offline detection, graceful degradation, "Back Online" recovery, stale
data indicators.

- PASS: Offline behavior is explicitly described
- FLAG: No mention of offline behavior for a feature that clearly makes network calls
- N/A: Feature is purely local/offline-first with no network calls

---

### Check 4 — Empty / zero-data states

**Question:** What does the user see when there is no data to display?

Applies to: lists, tables, dashboards, counts, search results, maps.

Look for: empty state copy, placeholder UI, hidden vs. zero-count display.

Also check: if filters are applied, do aggregate metrics (header counts, totals)
update to match, or are they intentionally static? If static, is that called out?

**Warning states must not render for zero counts**
A warning card, badge, or indicator should never appear when the count it
represents is zero. A zero count is not a warning condition — showing amber/red
for zero misleads the user into thinking action is required. Check any warning
UI elements introduced by the PR and verify they are conditionally hidden when
the underlying count is 0.

- PASS: Empty state and filter/count behavior are addressed; warning states are gated on count > 0
- FLAG: Empty state not mentioned for a list/table/dashboard feature; or warning UI renders for zero count
- N/A: Feature has no list or data display

---

### Check 5 — Action affordance & discoverability

**Question:** Is it clear to the user what is tappable or interactive?

Look for: visual affordance on interactive elements (buttons, links, toggles,
clickable rows), correct scoping of click targets, dismissal of modals (click
outside to close), hover states where relevant.

Check the Figma mocks reference in the ticket if present — are interactive
affordances (edit icons, toggle states, action buttons) accounted for in the PR?

- PASS: Interactive elements have clear affordance described or shown
- FLAG: Interactive element with no described affordance, or ambiguous tap target scope
- N/A: Feature has no interactive UI elements (view-only)

---

### Check 6 — Breadcrumb placement

**Question:** If the page introduces or modifies a full page view, does it include
a breadcrumb, and is it the first element in the content area?

Breadcrumbs must always appear at the top of the page content, before any titles,
KPI strips, tables, or other content. In templates this means
`{% include 'components/breadcrumbs.html' %}` must be the first child inside the
content wrapper `<div>`.

- PASS: Breadcrumb is present and is the first element in the content area
- FLAG: Breadcrumb is missing from a page-level view, or is present but not at the top
- N/A: Change affects only a modal, partial/fragment, or component — not a full page

---

### Check 7 — Copy & helper text

**Question:** Is all user-facing text clear, consistent with Connect terminology,
and non-redundant?

Look for:
- Correct role names (Program Manager, Front Line Worker — not "user" or "admin")
- Helper text under form fields explaining what the field is for
- Error messages that describe what went wrong and what to do
- No duplicate text (same info shown twice in different places)
- Column headers, button labels, and dialog titles are descriptive

- PASS: Copy appears consistent and complete based on ticket description
- FLAG: Specific copy gap or inconsistency identified — call it out explicitly
- N/A: No user-facing text changes

---

### Check 8 — Numerical value display

**Question:** Are numerical values formatted correctly throughout the UI?

Scan changed templates and Python rendering code for the following rules:

**Percentages — no decimal places**
Percentage values must be displayed as whole numbers. `97.33%` is a violation;
`97%` is correct. Look for: `round()`, `:.0f`, or equivalent in Python rendering;
in templates check for any `%` values being passed through without rounding.

**Small decimals — two decimal places maximum**
Any non-percentage decimal value between -1 and 1 (exclusive) must be rounded to
2 decimal places. `0.543435` is a violation; `0.54` is correct. Look for float
values rendered directly without a rounding step.

**Currency — always show the currency indicator**
Any monetary amount must be accompanied by its currency code or symbol. A bare
number like `1,250` is a violation when representing a currency value; `1,250
(USD)` or `$1,250` is correct. The codebase convention is to display the currency
code after the amount: `{{ amount }} ({{ currency }})`.

- PASS: All numerical values in changed code follow the formatting rules above
- FLAG: Identify each violation with filename, the offending value/expression, and the correct format
- N/A: PR introduces no numerical display changes

---

### Check 9 — Spec / wireframe alignment

**Question:** Does the implementation match the ticket's acceptance criteria and
Figma mocks? Are any intentional deviations called out?

Look for:
- Acceptance criteria items that are unaccounted for in the PR description
- Deviations from wireframes that are not flagged by the developer
- Scope additions (things implemented beyond what the ticket asked for) that
  haven't been noted

- PASS: PR description addresses all acceptance criteria; deviations are called out
- FLAG: Unaddressed acceptance criteria items, or undisclosed deviation from spec
- N/A: Ticket has no acceptance criteria or wireframes

---

### Check 10 — Transition & animation polish

**Question:** Are there any UI transitions or state changes that could appear
jarring or confusing?

Look for: loading bar → success banner switching rapidly, modal open/close
animations, page navigation smoothness.

- PASS: No jarring transitions apparent, or transitions are explicitly addressed
- FLAG: Rapid state switching or animation behavior not addressed
- N/A: No animated or transitioning UI elements

---

### Check 11 — Navigation & wayfinding

**Question:** Can the user navigate to and from this page/feature without relying
on the browser back button or the sidebar?

Every page in the app must be reachable and leavable via breadcrumbs alone.
Specific rules derived from recurring feedback:

**No dead-end pages**
Every full page view must have a breadcrumb trail that lets the user navigate
back to any ancestor page. If the PR introduces a new page, check that its
breadcrumb chain is complete back to the Opportunity dashboard.

**No broken or non-functional links**
Any element styled as a link (underlined, blue, or with a `href`) must navigate
somewhere valid. Links that go to a 404, do nothing, or are placeholders are a
violation. This includes: table row links, ID columns, edit buttons, and ">"
carrot navigation icons. If a link has no valid destination yet, remove the link
styling until it does.

**Permission-gated actions must be hidden, not broken**
If a user lacks permission to perform an action (e.g. edit a task), the button
or link for that action must be hidden or visibly disabled — not shown and
silently failing. A "Failed to load" error on click for a non-permitted action
is a violation.

**Cross-page navigation shortcuts**
If the PR introduces a page that is logically related to another page (e.g.
worker tasks page relates to assigned tasks page), check whether a navigation
shortcut (tab, breadcrumb, or "See more" link) exists to get between them.

- PASS: All links are functional; no dead-end pages; permission-gated actions are hidden/disabled
- FLAG: Broken link, dead-end page, or permission-gated action that fails silently
- N/A: PR introduces no new pages or navigation elements

---

### Check 12 — Table layout & column headers

**Question:** Is the table readable without excessive horizontal scrolling, and
are column headers compact?

**Wrap column headers to two lines**
Long column header text is the primary driver of table width. Headers must wrap
onto two lines rather than forcing the table to expand horizontally. In
templates, check that column header `<th>` elements do not have `whitespace-nowrap`
or equivalent classes preventing wrapping. The preferred pattern is short header
text (≤3 words) or wrapped text using `break-words` / `whitespace-normal`.

**Freeze first column and header row on wide tables**
Any table with more than 6 columns must freeze the first column (typically the
worker name or ID) and the header row so users retain context when scrolling
horizontally or vertically. Check for `sticky` positioning on the first `<th>`
and `<td>` in each row, and on the `<thead>` row.

**No excessive column count without justification**
If a table introduces more than 8 columns, flag it — the PR or ticket should
justify the column count and confirm headers are wrapped. More columns than can
fit in a standard 1440px viewport without scrolling requires explicit sign-off.

- PASS: Headers wrap onto two lines; wide tables freeze first column and header row
- FLAG: Headers use `whitespace-nowrap` or equivalent; wide table lacks frozen column/header; unjustified column count
- N/A: PR introduces no tables, or table has ≤5 columns

---

### Check 13 — Status labels & dropdown option naming

**Question:** Are all status values, dropdown options, and filter labels named
clearly and consistently with the requirements doc?

Specific rules from recurring feedback:

**Status values must match the requirements doc exactly**
Do not invent status names. Known correct values:
- Work area status: `not_visited` (not `not_started`), `visited`, `inaccessible`, `excluded`
- Audit status: `Pending`, `Complete` (not `Done`, `Finished`, etc.)
- Visit status: `Approved`, `Pending`, `Rejected`

**Dropdown options must be meaningful**
Options like `Unknown` for a yes/no toggle are a violation. Every dropdown
option must have a clear, unambiguous meaning. If `Unknown` is a genuine state
(data not available), label it as `Not set` or `No data` instead.

**Filter labels must describe what they filter**
A filter labeled "Start Date" is ambiguous — "Visit Start Date" or "Report
Start Date" is correct. All filter labels must include the entity being filtered.

**UI labels must match feature names**
The label shown in the UI must match the feature's official name. Example:
"Verification Rules" must not appear as "Verification Flags" in the nav menu.

- PASS: All status values, dropdown options, and filter labels are correct and consistent
- FLAG: Status value doesn't match requirements doc; ambiguous dropdown option; filter label missing entity name; UI label mismatches feature name
- N/A: PR introduces no status values, dropdowns, or filter labels

---

### Check 14 — Completion confirmation feedback

**Question:** When a user completes a significant action (submitting a form,
completing an audit, finishing an upload), do they receive clear confirmation
that it succeeded?

Specific rules from recurring feedback:

**Every terminal action needs a confirmation**
Actions that complete a workflow (e.g. "Complete Audit", "Submit", "Save and
Confirm") must produce visible confirmation feedback. Acceptable patterns:
- A success banner at the top of the page
- A state change on the triggering element (button becomes disabled, label
  changes to "Completed")
- Navigation to a success/confirmation page

Silently doing nothing after a "Complete" action is a violation — the user
cannot tell if the action succeeded.

**Confirmation must be on the page, not just in a modal**
A confirmation that only appears inside a modal (which then closes) is
insufficient — the user needs persistent feedback on the underlying page.

- PASS: Terminal actions produce clear, persistent confirmation feedback
- FLAG: Terminal action has no visible confirmation; or confirmation only appears inside a closing modal
- N/A: PR introduces no terminal/completion actions

---

### Check 15 — Shared component usage

**Question:** Does the PR use the codebase's shared components where they exist,
rather than reimplementing equivalent UI from scratch?

The codebase has a component library in `commcare_connect/templates/components/`.
Using these components ensures consistency, correct token usage, and correct
behavior (dismiss, Escape, click-outside) without re-implementing it. Bypassing
them in favour of custom HTML is a violation.

**Confirmation dialogs → `components/confirm_modal.html`**
Any confirmation dialog (destructive or otherwise) must use the shared
`$store.confirmModal.show(...)` Alpine store. Custom inline confirmation overlays
(e.g. a bespoke `x-show="confirm"` div) are a violation. Additionally:
- Destructive actions (delete, reject, irreversible) must pass `confirmBtnRed: true`
  to the store — a purple confirm button on a destructive action is a violation.

**Filter panels → `components/filter_modal.html`**
Any page with filterable content must use `filter_modal.html` with `FilterMixin`
from the view. Inline filter panels, free-text filter inputs without the modal
pattern, or custom filter drawers are violations. The `filters_applied_count`
badge must be wired from the view — a filter modal with no count badge is an
incomplete integration.

**File import modals → `components/worker_page/import_modal.html`**
Any file upload modal must use the shared import modal component. Custom file
upload modals are violations.

**Progress bars → `components/progressbar/simple-progressbar.html`**
Any progress bar must use the shared component. Raw `<div>` elements with inline
`style="width: X%"` used as progress bars are violations. Note: the existing
`upload_progress_bar.html` component itself contains tech debt (raw hex colors,
`bg-purple-600`) — new PRs must not copy that pattern.

**Multi-select dropdowns → TomSelect via `[data-tomselect]`**
Any multi-select input must use TomSelect, initialized via the `[data-tomselect]`
attribute and `components/tomselect_init.html`. Raw `<select multiple>` elements
without TomSelect are violations.

**Post-action feedback → Django `messages` framework**
Success, error, and warning feedback after form submissions and view actions must
use `messages.success()`, `messages.error()`, or `messages.warning()` in the
view. These are rendered automatically by `base.html` with correct tokens, icons,
and dismiss behavior. Custom inline banner `<div>` elements constructed in
templates instead of using Django messages are violations.

**Sidenav active state must reflect current section**
The sidenav highlights the active section by comparing
`request.resolver_match.namespace` to the `namespace` parameter in
`components/sidenav-items.html`. Any PR that adds a new page or moves pages
between URL namespaces must verify the correct sidenav item is highlighted. An
unhighlighted or wrong-highlighted sidenav item is a violation.

**`bi-` icons are a violation**
Bootstrap Icons (`<i class="bi bi-...">`) must not appear in any new or modified
template. Only FA7 (`fa-solid`, `fa-regular`) is permitted. If a PR touches a
file that already contains `bi-` icons, those should be migrated to FA7
equivalents as part of the PR.

**Scan for violations:**
```bash
SHA=<HEAD_SHA>
BASE="https://raw.githubusercontent.com/dimagi/commcare-connect/$SHA"

# Check for custom confirmation overlays instead of confirm_modal
for f in <changed_html_files>; do
  content=$(curl -s "$BASE/$f")
  echo "$content" | grep -n "x-show.*confirm\|confirmBtnRed\|bi bi-" || true
done

# Check for inline progress bars
for f in <changed_html_files>; do
  curl -s "$BASE/$f" | grep -n 'style="width:.*%' || true
done

# Check for raw select multiple without tomselect
for f in <changed_html_files>; do
  curl -s "$BASE/$f" | grep -n '<select multiple' || true
done

# Check for inline banner divs instead of Django messages
for f in <changed_html_files>; do
  curl -s "$BASE/$f" | grep -n 'bg-message-success\|bg-message-error\|bg-message-warning' || true
  # These are only valid in base.html — flag if they appear elsewhere
done
```

- PASS: All UI patterns use the correct shared components; no custom reimplementations found
- FLAG: List each violation — which component was bypassed and what file/line
- N/A: PR contains no frontend template changes

---

### Check 16 — Codebase conventions

**Question:** Does the PR follow the established codebase conventions for dates,
nulls, pagination, tabs, loading, checkboxes, tooltips, and htmx error handling?

**Date/time formatting — use `DMYTColumn` and the format constants**
Any table column displaying a date or datetime must use `DMYTColumn` from
`commcare_connect/utils/tables.py`. Rendering datetimes directly produces ISO
or raw `YYYY-MM-DD HH:MM:SS` format — a violation. The constants are:
- `DATE_TIME_FORMAT = "%d-%b-%Y %H:%M"` (e.g. `18-Jun-2026 14:30`)
- `DATE_FORMAT = "%d-%b-%Y"` (e.g. `18-Jun-2026`)

In templates, dates must be filtered through `|date:"j N Y"` or rendered via
`DMYTColumn` — never rendered raw from a queryset or via Python's default
`str(datetime)`.

**Null/empty cell display — em dash `—` only**
Any null, missing, or unavailable value in a table cell or KPI tile must display
as an em dash `—`. Violations include: blank cells, `None` as a string, `N/A`,
`--` (double hyphen), or `0` used to represent "no data". `DMYTColumn.render()`
returns `"—"` for None automatically — any custom column rendering None must
do the same.

**Pagination — use `get_validated_page_size()` and `DEFAULT_PAGE_SIZE`**
Any view rendering a table must use `get_validated_page_size(request)` from
`commcare_connect/utils/tables.py` to set the page size. Hardcoded page sizes
and tables with no pagination are violations. Valid page size options are
`[20, 30, 50, 100]` with a default of 20.

**Tabs — `hx-push-url="true"` and active state via `url_name`**
Tab implementations must:
- Use `hx-push-url="true"` so the URL updates on tab switch (bookmarkable,
  back-button safe)
- Set the active state via `request.resolver_match.url_name` comparison —
  not via JavaScript state or custom active tracking
- Wire `hx-indicator="#loadingIndicator"` for the loading state

Tabs that don't update the URL, or use a custom active-state mechanism, are
violations.

**Loading indicator — wire `hx-indicator="#loadingIndicator"`**
Every page template that uses htmx for data loading already includes a
`<div id="loadingIndicator" class="loading-indicator htmx-indicator">`.
Every htmx request that fetches or loads data must include
`hx-indicator="#loadingIndicator"`. An htmx call with no loading indicator
leaves the user with no feedback during loading — a violation.

**Checkbox columns — use `select_column()` from `utils/tables.py`**
Any table with row selection checkboxes must use the `select_column()` factory
from `commcare_connect/utils/tables.py`, which wires Alpine's `selectAll`,
`selected`, and `toggleSelectAll()` correctly. Custom checkbox column
implementations are violations. Additionally, a checkbox column with no
visible bulk action bar (no button or action that appears when rows are
selected) is a violation — checkboxes must always have a purpose.

**Tooltips — use `x-tooltip.raw="..."` not title attributes**
All hover tooltips must use the Alpine `x-tooltip.raw="..."` directive. Native
HTML `title=""` attributes and custom `<div>` popup tooltip implementations
are violations.

**htmx form errors — use `HX-Trigger: form_error` header**
Views handling htmx form submissions must return validation errors as:
```python
return HttpResponseBadRequest(
    "Error message here",
    headers={"HX-Trigger": "form_error"},
)
```
The template listens for the `form_error` event to surface the message inline.
Returning an HTML fragment on error, redirecting on error, or using
`JsonResponse` for form validation errors are all violations of this pattern.

**Scan for violations:**
```bash
SHA=<HEAD_SHA>
BASE="https://raw.githubusercontent.com/dimagi/commcare-connect/$SHA"

for f in <changed_files>; do
  content=$(curl -s "$BASE/$f")
  ext="${f##*.}"

  if [[ "$ext" == "py" ]]; then
    # Check for hardcoded page sizes
    echo "$content" | grep -n "paginate.*per_page\|paginate_by\s*=" | grep -v "get_validated_page_size\|DEFAULT_PAGE_SIZE" || true
    # Check for htmx error responses not using HX-Trigger
    echo "$content" | grep -n "HttpResponseBadRequest" | grep -v "HX-Trigger" || true
  fi

  if [[ "$ext" == "html" ]]; then
    # Check for raw date rendering (no |date filter, no DMYTColumn)
    echo "$content" | grep -n "\.created\|\.updated\|\.date\b" | grep -v "|date\|DMYTColumn" || true
    # Check for title="" tooltips
    echo "$content" | grep -n 'title="' | grep -v "block title\|{% block" || true
    # Check for hx requests without loading indicator
    echo "$content" | grep -n "hx-get\|hx-post\|hx-put" | grep -v "hx-indicator\|hx-trigger.*load\b" || true
    # Check for null display violations
    echo "$content" | grep -n '"N/A"\|"None"\|"--"' || true
    # Check for raw select multiple without tomselect
    echo "$content" | grep -n "<select multiple" || true
  fi
done
```

- PASS: All codebase conventions followed in changed files
- FLAG: List each violation with filename, line, and the correct pattern to use
- N/A: PR contains no Python views or HTML templates

---

## Step 5: Generate the report

Write a Markdown file to `/mnt/user-data/outputs/<TICKET-ID>-ux-review.md`.

Use this structure:

```
# UX Review: <ticket summary>
[<TICKET-ID>](<ticket URL>) · [PR #<number>](<PR URL>)

---

**What this PR does**
<2–3 sentences describing what the PR changes, written for a reviewer who hasn't read the PR.>

---

**N flags**  ← total count up front

🔴 **<Title of most severe flag>** *(<filename> line <N>)*
<What the problem is, why it matters, what breaks if unaddressed.>
→ <Specific resolution in one line.>

🟠 **<Title of moderate flag>** *(<filename> line <N>)*
<Explanation.>
→ <Resolution.>

🟡 **<Title of minor flag>** *(<filename>)*
<Explanation.>
→ <Resolution.>

---

**Other notes**  ← use for non-flag observations (missing ticket link, pre-existing tech debt, etc.)
<Brief notes, one line each.>

---

**Demo checklist**
- [ ] <Specific scenario to show in the demo video>
- [ ] <Another scenario>
```

**Severity guide:**
- 🔴 Must fix before merging — broken behavior, silent failures, accessibility
- 🟠 Should fix before demo — design system violations, missing UX patterns
- 🟡 Nice to fix — copy, minor convention gaps, low-impact inconsistencies

**If there are no flags**, write: "No flags — feature looks ready for demo." and provide the demo checklist only.

Omit the "Other notes" section if there's nothing to add. Keep flag descriptions concise — one short paragraph + one resolution line each. The demo checklist should be specific to the feature, not generic.

---

## Dimagi role and terminology

Use precise role names throughout:

| Abbreviation | Full term |
|---|---|
| PM | Program Manager |
| NM | Network Manager |
| FLW | Front Line Worker |

---

## Notes on judgment

- A **FLAG** is not a blocker — it is a question or gap worth surfacing before
  the demo review. The developer may have a good reason for the current approach.
- Checks should be **N/A** liberally for features where they genuinely don't
  apply — don't force a FLAG on a read-only table for "action affordance".
- The **Demo checklist** at the end is the most actionable output — make it
  specific to the feature, not generic.
- If the PR description is thin but the ticket has detailed acceptance criteria,
  use the ticket as the primary source of truth.
