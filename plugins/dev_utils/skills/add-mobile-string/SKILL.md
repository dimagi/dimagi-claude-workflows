---
name: add-mobile-string
description: Use when the user asks to add a new Android string resource with translations to the CommCare Android project, given a string resource name and English text
---

# Add Android String Resource

## Overview

Add a new `<string>` entry to all locale `strings.xml` files in the CommCare Android project, given a resource name and English text.

## Discovering Locales

The English source lives at `app/res/values/strings.xml`. Translated locales live in sibling directories matching `app/res/values-*/strings.xml` (e.g., `values-es`, `values-fr`). Always enumerate the current set at runtime — do not assume a fixed list, since locales may be added or removed over time.

Run this to list every locale `strings.xml` file:

```bash
ls app/res/values*/strings.xml
```

The directory suffix after `values-` is the BCP 47 / Android locale code (e.g., `es` = Spanish, `fr` = French, `pt` = Portuguese). Translate accordingly.

## Workflow

1. **Enumerate locales:** Run the `ls` command above to get the full current set of locale files.
2. **Locate insertion point:** Grep for a nearby existing string with a similar prefix in `values/strings.xml` to find the right neighborhood. Place the new string near related entries.
3. **Read context around insertion point** in each locale file (the same neighboring strings may appear at different line numbers per locale).
4. **Add the English string** to `values/strings.xml`.
5. **Translate and add** to every other locale file discovered in step 1. Translate the English text into each language, matching the tone and style of surrounding strings in that file.
6. **Every locale gets the string** — do not skip any locale, even ones that have fewer existing strings.

## Product Names

Never translate product and brand names: **CommCare**, **CommCare HQ**, **Connect**, **PersonalID**, **Dimagi**. Keep them in English, spelled exactly as in the English source, inside every translated string. "Connect" is the product, not the verb, so it is not "Conectar", "Connecter" or "Ligar".

When the whole string is a product name (e.g. `<string name="connect_title">Connect</string>`), mark it `translatable="false"` in `values/strings.xml` and add it to no locale file.

## Format

```xml
<string name="resource_name">Translated text here</string>
```

- Escape apostrophes with `\'` in XML.
- Preserve any `%d`, `%s`, or other format specifiers exactly as in the English source.

## Common Mistakes

- Skipping locales that have fewer translated strings — always include every locale returned by the discovery step, regardless of how sparse the file is.
- Hard-coding a list of locales from memory instead of running the discovery command — the set of supported locales changes over time.
- Placing the string at the end of the file instead of near related strings.
- Forgetting to escape special XML characters in translations.
- Translating a product name such as "Connect" or "CommCare" as an ordinary word.
