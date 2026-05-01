---
name: add-mobile-string
description: Use when the user asks to add a new Android string resource with translations to the CommCare Android project, given a string resource name and English text
---

# Add Android String Resource

## Overview

Add a new `<string>` entry to all supported locale `strings.xml` files in the CommCare Android project, given a resource name and English text.

## Supported Locales

| Code | Language   | Path                          |
|------|------------|-------------------------------|
| en   | English    | `app/res/values/strings.xml`  |
| es   | Spanish    | `app/res/values-es/strings.xml` |
| fr   | French     | `app/res/values-fr/strings.xml` |
| ha   | Hausa      | `app/res/values-ha/strings.xml` |
| hi   | Hindi      | `app/res/values-hi/strings.xml` |
| lt   | Lithuanian | `app/res/values-lt/strings.xml` |
| no   | Norwegian  | `app/res/values-no/strings.xml` |
| pt   | Portuguese | `app/res/values-pt/strings.xml` |
| sw   | Swahili    | `app/res/values-sw/strings.xml` |
| ti   | Tigrinya   | `app/res/values-ti/strings.xml` |

## Workflow

1. **Locate insertion point:** Grep for a nearby existing string with a similar prefix in `values/strings.xml` to find the right neighborhood. Place the new string near related entries.
2. **Read context around insertion point** in each locale file (the same neighboring strings may appear at different line numbers per locale).
3. **Add the English string** to `values/strings.xml`.
4. **Translate and add** to every other locale file listed above. Translate the English text into each language, matching the tone and style of surrounding strings in that file.
5. **Every locale gets the string** — do not skip locales even if they have fewer existing strings.

## Format

```xml
<string name="resource_name">Translated text here</string>
```

- Escape apostrophes with `\'` in XML.
- Preserve any `%d`, `%s`, or other format specifiers exactly as in the English source.

## Common Mistakes

- Skipping locales that have fewer translated strings (e.g., lt, no) — always include all 10 locales.
- Placing the string at the end of the file instead of near related strings.
- Forgetting to escape special XML characters in translations.
