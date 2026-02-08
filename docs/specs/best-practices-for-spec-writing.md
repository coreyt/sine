# Best Practices for Writing Sine Rules

This document outlines the mistakes, learnings, and best practices for writing robust, validatable rules for Sine (and Semgrep). It is derived from real-world debugging of the initial rule set.

## 1. Metavariables and Identifiers
**Mistake:** Trying to concatenate metavariables with identifiers.
**Bad:** `pattern: def create_$NAME(...):`
**Why:** Semgrep cannot parse this in many languages (like Python) because `$NAME` is not a valid suffix for an identifier token.
**Fix:** Use generic identifiers and `metavariable-regex`.

**Good:**
```yaml
patterns:
  - |
    def $FUNC(...): ...
metavariable_regex:
  - metavariable: "$FUNC"
    regex: "^create_.*"
```

## 2. The Power of Ellipses (`...`)
**Mistake:** Over-specifying function arguments or bodies.
**Bad:** 
```python
def __init__(self, $DEP): 
    self.dep = $DEP
```
**Why:** 
1.  **Arguments:** This matches a function with *exactly* one argument (besides self). It fails if there are multiple dependencies.
2.  **Body:** This matches a function with *exactly* one statement. It fails if there is logging, super() calls, or other assignments.

**Fix:** Use ellipses (`...`) liberally to allow context.
**Good:**
```yaml
class $CLASS:
  def __init__(..., $DEP, ...):  # Match $DEP anywhere in args
    ...                          # Allow preceding statements
    self.$FIELD = $DEP           # The pattern we care about
```

## 3. Decorator Flexibility
**Mistake:** Assuming `@decorator` matches everything.
**Bad:** `pattern: @lru_cache`
**Why:** In Semgrep:
*   `@dec` matches the decorator object (e.g. `def f(): ...`).
*   `@dec(...)` matches the decorator call (e.g. `@lru_cache(maxsize=128)`).
**Fix:** Provide patterns for both or ensure you match the call if arguments are possible.

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
*   **Discovery Rules:** Should be **permissive**.
    *   **Goal:** Find *usage* of a pattern.
    *   **Strategy:** Match the **Interface** (signatures, types, decorators). Avoid matching implementation details (control flow, variable names) unless that logic *is* the pattern.
    *   *Example (Result Type):* Match `def f() -> tuple[bool, ...]: ...` instead of enforcing `if error: return False`.
*   **Enforcement Rules:** Should be **strict**.
    *   **Goal:** Prevent *bad* patterns.
    *   **Strategy:** Be specific to avoid false positives.

## 5. Examples are Tests
The `examples` section in your Rule Spec is not just documentation; it is the **regression test suite**.
*   **Good Examples:** MUST be matched by the pattern. If they don't match, the rule is broken.
*   **Bad Examples:** MUST NOT be matched by the pattern (or MUST match a "forbidden" pattern).
*   **Consistency:** If your pattern requires variable reassignment (e.g., Pipeline `$RES = f(); $RES = g($RES)`), your example must use it. Do not write "idiomatic" examples that conflict with "strict" patterns.

## 6. Complex Semgrep Features
Sine's `PatternDiscoveryCheck` is a simplified model. It supports:
*   `patterns` (list of strings, implicitly `pattern-either`)
*   `metavariable_regex`

If you need advanced Semgrep features (e.g., `pattern-inside`, `focus-metavariable`, logical `not`), use the **`RawCheck`** type to inject full Semgrep YAML configuration.

## 7. Troubleshooting Checklist
If your rule isn't matching:
1.  [ ] **Syntax:** Is the pattern valid Python? (e.g. `create_$NAME` is invalid).
2.  [ ] **Body:** Did you forget `...` in the function/class body?
3.  [ ] **Arguments:** Did you forget `...` in the argument list?
4.  [ ] **Decorators:** Did you handle `@dec` vs `@dec(...)`?
5.  [ ] **Metavariables:** Are you expecting `$VAR` to match distinct variables? (It won't; use distinct metavariables `$A`, `$B` or accept stricter matching).
6.  [ ] **Type Hints:** Semgrep handles them, but sometimes simplifying the pattern helps debug.