---
name: vertical-ordering
description: Use when writing new functions, extracting helpers, refactoring modules, or reorganizing code — any time function placement order is a decision
---

# Vertical Ordering

## Overview

Place caller functions above their callees. High-level logic first, implementation details below. Read top-down like a newspaper article.

This is the "Vertical Ordering" principle from Clean Code (Robert C. Martin, Chapter 5).

## Core Pattern

```python
# ✅ CORRECT: Caller above callee
def process_order(order):
    validate_order(order)
    submit_order(order)


def validate_order(order):
    ...


def submit_order(order):
    ...


# ❌ WRONG: Helpers defined before caller
def validate_order(order):
    ...


def submit_order(order):
    ...


def process_order(order):
    validate_order(order)
    submit_order(order)
```

## Quick Reference

| Scenario | Ordering |
|---|---|
| Extract a helper from a function | Helper goes **below** the function it was extracted from |
| Public API function calls private helpers | Public function first, private helpers below |
| Chain of calls: A → B → C | Order: A, then B, then C |
| Multiple callers share a helper | Helper goes below its first caller |

## Common Mistakes

- **Defining before use** — feels natural (like variable declaration) but hides the high-level flow. Readers see details before context.
- **Alphabetical ordering** — ignores call relationships. The reader has to jump around to follow the logic.
- **Grouping all helpers at the top or bottom** — loses the locality of related functions. Keep caller and callee close together.
