# Best Practices for Writing Sine Rules

This document outlines the mistakes, learnings, and best practices for writing robust, validatable rules for Sine (and Semgrep).

## 1. Metavariables and Regex
**Mistake:** Trying to concatenate metavariables with identifiers.
**Bad:** `def create_$NAME(...):`
**Why:** Semgrep cannot parse this in many languages (like Python) because `$NAME` is not a valid suffix for an identifier token.
**Fix:** Use `metavariable-regex` to enforce naming conventions.

**Good:**
```yaml
patterns:
  - |
    def $FUNC(...): ...
metavariable_regex:
  - metavariable: "$FUNC"
    regex: "^create_.*"
```

## 2. Flexibility with Ellipses (`...`)
**Mistake:** Over-specifying function arguments or bodies.
**Bad:** `def __init__(self, $DEP): self.dep = $DEP`
**Why:** This matches a function with *exactly* one argument (besides self) and *exactly* one statement. It will miss `def __init__(self, dep1, dep2): ...` or functions with logging/validation.

**Fix:** Use ellipses (`...`) liberally.
**Good:**
```yaml
class $CLASS:
  def __init__(..., $DEP, ...):  # Match $DEP anywhere in args
    ...                          # Allow preceding statements
    self.$FIELD = $DEP           # The pattern we care about
```

## 3. Decorator Patterns
**Mistake:** Assuming `@decorator` matches `@decorator(arg=1)`.
**Bad:** `pattern: @lru_cache`
**Why:** In Semgrep, `@dec` often matches the decorator *object* (no call), whereas `@dec(...)` matches the *call*.
**Fix:** Provide patterns for both or use ellipses.

**Good:**
```yaml
pattern-either:
  - |
    @lru_cache
    def $F(...): ...
  - |
    @lru_cache(...)
    def $F(...): ...
```

## 4. Discovery vs. Enforcement
**Discovery Rules:** Should be **permissive**.
*   **Goal:** Find where a pattern is used.
*   **Strategy:** Match signatures or key structural markers. Avoid coupling to specific implementation details (like `if/else` order) unless that logic *is* the pattern.
*   **Example (Result Type):** Match `def f() -> tuple[bool, ...]: ...` rather than enforcing `if error: return False`.

**Enforcement Rules:** Should be **strict**.
*   **Goal:** Prevent bad patterns.
*   **Strategy:** Be specific to avoid false positives.

## 5. Examples are Tests
The `examples` section in your Rule Spec is not just documentation; it is the **regression test suite**.
*   **Good Examples:** MUST be matched by the pattern. If they don't match, the rule is broken.
*   **Bad Examples:** MUST NOT be matched by the pattern (or MUST match a "forbidden" pattern).
*   **Consistency:** If your pattern requires variable reassignment (e.g., Pipeline), your example must use it. Do not write "idiomatic" examples that conflict with "strict" patterns.

## 6. Complex Semgrep Features
Sine's `PatternDiscoveryCheck` is a simplified model. It supports:
*   `patterns` (list of strings, implicitly `pattern-either`)
*   `metavariable_regex`

If you need advanced Semgrep features (e.g., `pattern-inside`, `focus-metavariable`, logical `not`), use the **`RawCheck`** type to inject full Semgrep YAML configuration.

## Checklist for New Rules
1.  [ ] Does the pattern use `...` in function bodies?
2.  [ ] Does the pattern use `...` in argument lists?
3.  [ ] Are metavariables standalone (not `prefix_$VAR`)?
4.  [ ] Do the `good` examples actually match the pattern logic?
5.  [ ] Is the code in `examples` syntactically valid for the target language?
