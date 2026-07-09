# Worked example

A realistic small change: the SSO token was not re-fetched after the server returned an "invalid token" error, forcing users to log in again. The fix re-fetches once and retries. Branch `CCCT-1929-refetch-sso-token`, author ran the flow on a device.

This shows the *shape and length* to aim for. Real output scales with the change — a one-line fix gets less than this, a large feature gets a bit more, but the density stays the same.

---

## Title

```
CCCT-1929 Re-Fetch SSO Token On Invalid Token Error
```

## RELEASES.md — Release Notes

Under `#### Important Bug Fixes`:

```
- Fixed an issue where an expired session could unexpectedly log users out instead of refreshing automatically.
```

## RELEASES.md — QA Notes

```
- Confirm that leaving the app idle long enough for the session to expire, then resuming, keeps you logged in instead of bouncing you to the login screen.
```

One bullet — it is the only user-observable, non-obvious risk. No step-by-step.

## PR description

```markdown
### [CCCT-1929](https://dimagi.atlassian.net/browse/CCCT-1929)

## Safety story

**What gives confidence**
- I reproduced the original logout on a device, then confirmed the fix keeps the session alive across an expiry.
- Change is scoped to the auth interceptor; no other call sites touched.

**Risks to review**
- The retry is not covered by an automated test; the retry-once guard is verified only by my manual run.
- Behavior change on the auth path — worth a second look at the loop guard so a persistently invalid token can't retry forever.

## Technical Summary

The auth interceptor now treats an "invalid token" response as a signal to re-fetch the SSO token once and retry the original request, rather than surfacing the failure. A one-shot guard prevents a refetch loop when the refreshed token is also rejected.
```

Note what is **absent**: no Product Description (no new user-facing capability — a bug fix, covered by the release note), no Automated test coverage section (no tests added), no Labels/Review section, no file-by-file walkthrough. Each omitted section is dropped whole, not filled with filler.

## Calibration: applying the diff test to a Technical Summary

A different change — adding one Firebase analytics event for the Manage Profile screens. First draft:

> ❌ Adds a single `personal_id_manage_profile_action` Firebase event for the Manage Profile screens, carrying a `manage_profile_action` parameter that distinguishes the actions (`photo_updated`, `name_updated`, `changes_discarded`) instead of one event per action. It is emitted through a new `FirebaseAnalyticsUtil.reportPersonalIdProfileAction` helper following the existing event/param/value convention. Screen opens and email verification are deliberately excluded — they are already captured by the auto `SCREEN_VIEW` and `OTP_REQUESTED` events.

Run the diff test on each clause. The event name, the param name, the action values, the helper name, "follows the existing convention" — a reviewer sees all of that in the diff. Cut. What remains is the two things the code can't say: the single-event-with-param *choice*, and *why* screen opens and email are excluded.

> ✅ Uses one event with an action parameter rather than one event per action. Screen opens and email verification are excluded — the auto `SCREEN_VIEW` and `OTP_REQUESTED` events already cover them, so logging them here would double-count.

Two sentences, zero restatement.

## Suggested Review Order comment

```markdown
## Suggested Review Order

- `AuthInterceptor.kt` — the refetch-and-retry logic and the loop guard; the whole change lives here
- `TokenRepository.kt` — supporting `refreshToken()` the interceptor calls
```
