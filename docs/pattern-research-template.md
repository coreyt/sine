# Pattern Research Template

> **Purpose**: Fill this out via deep research / LLM web search, then provide to Lookout to generate a complete `PatternSpecFile` (schema v2 YAML).
>
> **Instructions**: Complete each section. Use `[UNKNOWN]` for fields you couldn't determine. Mark optional fields with `[SKIP]` to omit them. For Semgrep patterns, provide your best approximation — they will be validated before merging.

---

## 1. Pattern Specification (top-level)

### Identity

| Field | Value |
|-------|-------|
| **ID** | _e.g., `DI-001`, `CQRS-002`_ |
| **Title** | _Short name, e.g., "Dependency Injection via Constructor"_ |
| **Category** | _One of: `architecture`, `security`, `reliability`, `testing`, `performance`_ |
| **Subcategory** | _Optional. e.g., `dependency-injection`, `data-access`, `error-handling`_ |
| **Tags** | _Comma-separated. e.g., `solid, testability, decoupling`_ |
| **Tier** | _1 (must-fix), 2 (should-fix), 3 (advisory)_ |
| **Severity** | _One of: `error`, `warning`, `info`_ |
| **Confidence** | _One of: `low`, `medium`, `high` — how reliably does the pattern detect real issues?_ |

### Description

**What this pattern enforces** (2-4 sentences):
> _Describe the coding practice this pattern checks for. What should developers do? What should they avoid?_

**Rationale** (2-4 sentences):
> _Why does this matter? What problems occur when this pattern is violated?_

**Default violation message** (single line, shown to developers):
> _e.g., "Direct dependency instantiation in constructor — use injection instead (DI-001)"_

### References

List authoritative sources (Martin Fowler, language docs, seminal papers, etc.):

1. _URL + brief description_
2. _URL + brief description_
3. _URL + brief description_

### Detection Strategy

**What makes this pattern detectable by static analysis?**
> _Describe the syntactic or structural code signal. e.g., "A class constructor that calls `new` on a dependency rather than accepting it as a parameter."_

**Known false positive scenarios:**
> _When would a match NOT be a real violation? e.g., "Factory classes that are supposed to instantiate objects."_

**Known false negative scenarios:**
> _What violations would this miss? e.g., "Dependencies created via factory functions rather than constructors."_

---

## 2. Pattern-Language Specification

> Copy this section for each target language. The "generic" variant catches the base pattern without framework-specific assumptions.

### Language: `[LANGUAGE]`

| Field | Value |
|-------|-------|
| **Language** | _e.g., `python`, `typescript`, `java`, `go`, `csharp`_ |
| **Version constraint** | _Optional. e.g., `>=3.10`, `>=4.0`. Use `[SKIP]` if none._ |

#### Generic Variant

**Check type**: _One of: `forbidden`, `must_wrap`, `required_with`, `raw`, `pattern_discovery`_

**Semgrep pattern(s)**:
```
[Provide Semgrep pattern using the target language syntax.
Use metavariables: $CLS, $FUNC, $FIELD, $DEP, $X, $Y, etc.
Use ... for "any code" ellipsis matching.]
```

**If `must_wrap`**: target = `[list of functions/calls to wrap]`, wrapper = `[list of wrappers]`
**If `required_with`**: if_present = `[decorator/annotation]`, must_have = `[required companion]`
**If `raw`**: provide complete Semgrep rule YAML (including `patterns:`, `pattern-either:`, `pattern-not-inside:`, `metavariable-regex:`, etc.)

**Good example** (code that FOLLOWS the pattern):
```[language]
[2-10 lines of idiomatic code that would NOT trigger a violation]
```

**Bad example** (code that VIOLATES the pattern):
```[language]
[2-10 lines of code that WOULD trigger a violation]
```

**Language-specific notes:**
> _Any quirks, idioms, or considerations for this language. e.g., "Python uses `__init__` for constructors; Go uses factory functions instead of constructors."_

---

## 3. Pattern-Language-Framework Specification

> Copy this section for each framework variant within a language. Framework variants override or refine the generic pattern for framework-specific idioms.

### Framework: `[FRAMEWORK]` (Language: `[LANGUAGE]`)

| Field | Value |
|-------|-------|
| **Framework name** | _e.g., `django`, `angular`, `spring`, `express`, `gin`_ |
| **Version constraint** | _Optional. e.g., `>=4.0`, `>=14.0,<18.0`. Use `[SKIP]` if none._ |

**Why a separate variant?**
> _What framework-specific idiom makes the generic pattern insufficient? e.g., "Django views inherit from View and use super().__init__(); Angular uses @Injectable() decorator for DI."_

**Check type**: _One of: `forbidden`, `must_wrap`, `required_with`, `raw`, `pattern_discovery`_

**Semgrep pattern(s)**:
```
[Framework-specific Semgrep pattern. Reference framework base classes,
decorators, annotations, etc.]
```

**If `raw`**: provide complete Semgrep rule YAML.

**Good example** (framework-idiomatic code that follows the pattern):
```[language]
[2-10 lines showing proper framework usage]
```

**Bad example** (framework code that violates the pattern):
```[language]
[2-10 lines showing the violation in framework context]
```

**Framework-specific notes:**
> _Common patterns, migration guides, or framework documentation references._

---

## Research Checklist

Before submitting, verify:

- [ ] **Pattern is statically detectable** — Semgrep can match it structurally (not runtime behavior)
- [ ] **Each language variant compiles** — patterns use correct syntax for that language's Semgrep support
- [ ] **Good/bad examples are realistic** — not toy code; something a developer would actually write
- [ ] **False positives documented** — known cases where the pattern matches non-violations
- [ ] **References are authoritative** — not blog spam; prefer original sources, official docs, seminal papers
- [ ] **Framework variants are justified** — only add a framework variant if the generic one is insufficient
- [ ] **Check type is appropriate**:
  - `forbidden` — single pattern to flag (simplest)
  - `must_wrap` — call X must be inside wrapper Y
  - `required_with` — decorator A requires companion decorator B
  - `raw` — complex multi-pattern rules (pattern-either, pattern-not-inside, etc.)
  - `pattern_discovery` — descriptive (find instances), not prescriptive (find violations)

---

## Semgrep Pattern Quick Reference

| Construct | Meaning |
|-----------|---------|
| `$X` | Metavariable — matches any expression |
| `$...X` | Spread metavariable — matches zero or more arguments |
| `...` | Ellipsis — matches any sequence of statements |
| `$FUNC(...)` | Function call with any arguments |
| `class $CLS: ...` | Any class definition (Python) |
| `class $CLS { ... }` | Any class definition (TS/Java) |
| `pattern-either` | Match ANY of the listed patterns |
| `pattern-not-inside` | Exclude matches inside a larger pattern |
| `metavariable-regex` | Constrain a metavariable to match a regex |

**Supported languages**: python, javascript, typescript, java, go, ruby, csharp, kotlin, swift, rust, scala, php, lua, c, cpp, ocaml, r, solidity, terraform, json, yaml, html, xml, dockerfile, bash

---

## Example: Completed Template

<details>
<summary>Click to expand — DI-001 Dependency Injection (abbreviated)</summary>

### 1. Pattern Specification

| Field | Value |
|-------|-------|
| **ID** | `DI-001` |
| **Title** | Dependency Injection via Constructor |
| **Category** | `architecture` |
| **Subcategory** | `dependency-injection` |
| **Tags** | `solid, testability, decoupling` |
| **Tier** | 2 |
| **Severity** | `warning` |
| **Confidence** | `medium` |

**What this pattern enforces**: Classes should receive dependencies through constructor parameters rather than creating them internally. This enables testing with mocks, improves flexibility, and makes dependency relationships explicit.

**Rationale**: Hard-coded dependencies make classes difficult to test in isolation, tightly couple components, and hide the dependency graph. Constructor injection makes dependencies visible and swappable.

**Default violation message**: `Direct dependency instantiation in constructor — use injection instead (DI-001)`

**References**:
1. https://martinfowler.com/articles/injection.html — Martin Fowler's original article on DI
2. https://en.wikipedia.org/wiki/Dependency_injection — Overview with examples

**Detection strategy**: A class constructor that instantiates a dependency (calls a constructor/`new`) and assigns it to a field, rather than accepting it as a parameter.

**False positives**: Factory classes, builder patterns, value objects created in constructors.

**False negatives**: Dependencies created via static factory methods, service locator pattern.

### 2. Language: `python`

| Field | Value |
|-------|-------|
| **Version constraint** | `>=3.10` |

**Check type**: `raw`

```yaml
rules:
  - id: di-001-python-impl
    languages: [python]
    severity: WARNING
    message: "Direct dependency instantiation in constructor — use injection instead (DI-001)"
    patterns:
      - pattern: |
          class $CLS:
            def __init__(self, ...):
              self.$FIELD = $DEP(...)
```

**Good**:
```python
class OrderService:
    def __init__(self, repo: OrderRepository):
        self._repo = repo
```

**Bad**:
```python
class OrderService:
    def __init__(self):
        self._repo = OrderRepository()
```

### 3. Framework: `django` (Language: `python`)

| Field | Value |
|-------|-------|
| **Version constraint** | `>=4.0` |

**Why separate**: Django views inherit from `View` and use `super().__init__()`; the generic pattern should be narrowed to View subclasses to reduce false positives.

**Check type**: `raw`

```yaml
rules:
  - id: di-001-python-django-impl
    languages: [python]
    severity: WARNING
    message: "Django view creates service directly in constructor — use injection instead (DI-001)"
    patterns:
      - pattern: |
          class $VIEW(View):
            def __init__(self, ...):
              self.$SVC = $SVC_CLASS(...)
```

</details>
