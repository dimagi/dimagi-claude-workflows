# Language and Framework Notes

Idiomatic patterns, common pitfalls, and framework conventions. Each agent should consult the relevant section when reviewing code in that language/framework. These are supplements to the core dimension checklists — do not limit review to only what's listed here.

**Coverage**: Python, Django, JavaScript/TypeScript, React, Node.js, Go, Java/Kotlin, SQL. For languages not listed (Rust, Ruby, C/C++, Swift, etc.), fall back to the core checklists in your agent instructions — they apply broadly across languages.

---

## Python

**Pythonic idioms to check**
- `enumerate()` not `range(len(x))`
- `zip()` for parallel iteration
- List/dict/set comprehensions where they improve clarity (flag if nested 2+ levels)
- `x is None` / `x is not None` (not `x == None`)
- `with` statements for resource management (files, locks, connections)
- `@dataclass` or `NamedTuple` instead of plain dicts for structured data
- `pathlib.Path` over string path manipulation
- `secrets` module for security-sensitive random values (not `random`)

**Classic Python bugs**
- Mutable default arguments: `def foo(items=[])` — items is shared across all calls
- `except Exception` or bare `except:` swallowing errors silently
- `from module import *` polluting the namespace
- String concatenation in loops — use `"".join()`
- Comparing to `True`/`False` explicitly: `if x == True` instead of `if x`
- `global` keyword in non-trivial application code

**Type hints**
- Missing type hints on public function signatures
- Using `Optional[X]` vs `X | None` — should be consistent across the codebase
- `Any` used as a cop-out rather than typing properly

**Testing (pytest)**
- Tests with no assertions or trivially-true assertions
- Overuse of `mock.patch` hiding real design coupling
- Not using `pytest.fixture` for shared setup
- Not using `pytest.mark.parametrize` for repetitive test cases

---

## Django

**ORM and database**
- N+1 query problem: iterating over a queryset and accessing related objects without `select_related()` / `prefetch_related()`
- `.all()` in a tight loop without filtering — fetches everything into memory
- `.get()` without handling `DoesNotExist`
- Missing `db_index=True` on frequently-filtered ForeignKey or fields used in WHERE clauses
- Business logic in migrations — migrations should only transform data structures
- Relying on `Meta.ordering` for correctness in code — always specify ordering explicitly when it matters
- Missing `select_for_update()` in transactional code that reads then writes

**Views and security**
- Views that don't check `request.user.is_authenticated` or object-level permissions
- Passing `request.POST` or `request.GET` directly to models without cleaning via a Form/Serializer
- Missing `@login_required` or `LoginRequiredMixin`
- `ModelForm` without restricting `fields` (exposes all model fields to mass assignment)
- CSRF exemptions broader than needed

**Architecture**
- Business logic in views — should be in models, services, or a dedicated logic layer
- Business logic in DRF serializers
- Signals used to implement business logic (makes flow impossible to trace; prefer explicit calls)
- Fat models accumulating unrelated responsibilities — move to a service layer
- `settings.py` importing from app modules (circular import risk)

**Celery**
- Tasks that are not idempotent (retries cause duplicate side effects)
- Passing model instances as task arguments — use PKs; instances go stale across serialization
- Missing `bind=True` when using `self.retry()`
- No retry or error handling for tasks that call external services
- Very long-running tasks without chunking — blocks workers

---

## JavaScript / TypeScript

**General JS**
- `var` instead of `const` / `let`
- `==` instead of `===`
- Unhandled Promise rejections (`.then()` without `.catch()`, or `async` functions without try/catch)
- `async` functions that never `await` anything
- `console.log` left in non-debug code
- Mutating function arguments (especially objects/arrays passed by reference)

**TypeScript**
- `any` used to silence type errors
- Non-null assertions (`!`) used liberally without justification
- `@ts-ignore` without an explanation comment
- Not leveraging discriminated unions for state modelling

**React**
- Missing dependency arrays in `useEffect` / `useCallback` / `useMemo`
- Array index used as `key` in lists that can reorder
- Derived state stored in state (should be computed)
- Prop drilling more than 2–3 levels deep (consider context or composition)
- Large components combining data-fetching, transformation, and rendering
- Missing error boundaries for components that might throw
- Expensive operations in render without `useMemo`

**Node.js**
- Blocking the event loop with synchronous I/O (`fs.readFileSync` in request handlers)
- Not handling `error` events on streams
- Using `process.env` directly without validation or defaults
- Missing input validation on API endpoints

---

## Go

- Not checking returned errors
- Goroutine leaks (goroutines started with no cancellation mechanism)
- Not using `context.Context` for cancellation in long-running operations
- Not closing `http.Response.Body`
- Using `panic` for recoverable errors instead of returning them
- Exported identifiers without documentation comments
- Unbuffered channels causing unexpected blocking

---

## Java / Kotlin

**Java**
- Null pointer dereferences — not checking for null
- Catching `Exception` or `Throwable` too broadly
- `equals()` overridden without `hashCode()`
- Mutable static state (thread-safety)
- Not using try-with-resources for `Closeable`s
- String concatenation in loops — use `StringBuilder`

**Kotlin**
- `!!` (not-null assertion) without justification
- `lateinit var` on things that should be constructor-injected
- Not using `sealed class` + `when` for exhaustive state handling
- Coroutine scope leaks — coroutines outliving their intended lifecycle

---

## SQL

- `SELECT *` in application queries (fragile, over-fetches)
- Missing indexes on JOIN conditions and WHERE clause columns
- N+1 patterns — running queries inside loops
- Non-parameterised queries (injection risk)
- No transactions where atomicity is needed
- No LIMIT on queries that could return unbounded results
- Storing comma-separated values in a single column instead of a join table
- NULLs not handled consistently

---

## Cross-language Security Patterns

Regardless of language:
- User-controlled data in system calls, shell commands, `eval`
- Sensitive data in URLs (appears in logs and browser history)
- Predictable/sequential resource IDs (enumeration attacks)
- Missing rate limiting on auth endpoints
- JWT secrets hardcoded or too short
- CORS policies allowing `*` on credentialed endpoints
- Redirect URLs not validated (open redirect)
