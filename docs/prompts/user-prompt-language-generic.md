# User Prompt: Language-Generic Variant Specification

> **Usage**: After the top-level pattern spec is reviewed, send this prompt to generate language-specific generic variants. The `{{TOP_LEVEL_SPEC}}` placeholder is replaced with the approved Section 1 output.

```
## Task

Generate the **Language-Generic Variant** (Section 2) for the following pattern and language.

### Approved Top-Level Specification

{{TOP_LEVEL_SPEC}}

### Target Language

**Language**: {{LANGUAGE}}
**Language version constraint**: {{VERSION_CONSTRAINT_OR_SKIP}}

## Instructions

1. Research how this pattern manifests specifically in {{LANGUAGE}}:
   - What are the idiomatic constructs? (e.g., Python uses `__init__`, Go uses factory functions, Java uses constructors)
   - What existing linters already detect this? (e.g., pylint, eslint rules) — study their approach.
   - What are the language-specific false positive risks?

2. Write a Semgrep rule that detects violations (or instances, for discovery patterns).
   - Use {{LANGUAGE}}'s actual syntax in the pattern — not pseudocode.
   - Choose the simplest check type that works (`forbidden` > `must_wrap` > `required_with` > `raw`).
   - If you need `raw`, provide the COMPLETE Semgrep rule YAML including:
     - `id`: `{{PATTERN_ID_LOWER}}-{{LANGUAGE}}-impl`
     - `languages`: `[{{LANGUAGE}}]`
     - `severity`: matching the top-level spec
     - `message`: the default_message from the top-level spec
     - All `patterns:`, `pattern-either:`, `pattern-not-inside:`, `metavariable-regex:` as needed

3. Provide realistic good and bad code examples (3-12 lines each).

## Output Format

---

### Language: `{{LANGUAGE}}`

| Field | Value |
|-------|-------|
| **Language** | `{{LANGUAGE}}` |
| **Version constraint** | `{{VERSION_CONSTRAINT_OR_SKIP}}` |

#### Generic Variant

**Check type**: _(`forbidden`, `must_wrap`, `required_with`, `raw`, or `pattern_discovery`)_

**Semgrep pattern(s)**:
```yaml
[If raw, provide complete rule YAML]
[If forbidden/must_wrap/etc., provide just the pattern string]
```

**Good example** (code that FOLLOWS the pattern — must NOT match):
```{{LANGUAGE}}
[3-12 lines of idiomatic, correct code]
```

**Bad example** (code that VIOLATES the pattern — MUST match):
```{{LANGUAGE}}
[3-12 lines of realistic violating code]
```

**Language-specific notes:**
> [Idioms, quirks, common alternative approaches in this language]

---

## Quality Checklist

Before outputting, verify:
- [ ] Pattern uses {{LANGUAGE}}'s actual syntax (not pseudocode or another language's syntax)
- [ ] Good example does NOT match the pattern (mentally trace through)
- [ ] Bad example DOES match the pattern (mentally trace through)
- [ ] Rule ID follows the convention: `{{PATTERN_ID_LOWER}}-{{LANGUAGE}}-impl`
- [ ] Check type is the simplest that works for this detection
- [ ] Examples are realistic production code, not toy snippets
- [ ] Language-specific notes mention relevant idioms or alternative patterns
- [ ] If `raw`, the YAML is valid and the rule structure is correct (patterns is a list of objects)
```
