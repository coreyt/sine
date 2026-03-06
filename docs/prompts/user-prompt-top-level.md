# User Prompt: Top-Level Pattern Specification

> **Usage**: Send this prompt (with System Prompt) to generate the pattern-level specification only. After review, inject the result into the language-specific and framework-specific user prompts.

```
## Task

Generate the **top-level Pattern Specification** (Section 1 only) for the following pattern:

**Pattern ID**: {{PATTERN_ID}}
**Pattern Title**: {{PATTERN_TITLE}}
**Description hint**: {{DESCRIPTION_HINT}}

Use deep research to produce an authoritative, complete specification. Search for:
- The original definition and seminal references for this pattern/anti-pattern
- How major style guides (Google, Airbnb, Microsoft) treat this pattern
- Real-world incidents or bugs caused by violating this pattern
- Static analysis tools that already detect this (ESLint, Pylint, SonarQube, etc.) — study their detection strategies

## Output Format

Fill out ONLY Section 1 of the template below. Do not generate language or framework variants yet.

---

### 1. Pattern Specification

#### Identity

| Field | Value |
|-------|-------|
| **ID** | `{{PATTERN_ID}}` |
| **Title** | |
| **Category** | _One of: `architecture`, `security`, `reliability`, `testing`, `performance`_ |
| **Subcategory** | _Optional_ |
| **Tags** | _Comma-separated_ |
| **Tier** | _1 (must-fix), 2 (should-fix), 3 (advisory)_ |
| **Severity** | _One of: `error`, `warning`, `info`_ |
| **Confidence** | _One of: `low`, `medium`, `high`_ |

#### Description

**What this pattern enforces** (2-4 sentences):
>

**Rationale** (2-4 sentences):
>

**Default violation message** (single line, shown to developers inline with findings):
>

#### References

Provide 2-5 authoritative references. Every URL must be real.

1.
2.
3.

#### Detection Strategy

**What makes this pattern detectable by static analysis?**
> Describe the syntactic or structural code signal.

**Known false positive scenarios:**
> When would a match NOT be a real violation?

**Known false negative scenarios:**
> What violations would this miss?

#### Target Languages

List the languages where this pattern is relevant and briefly note any language-specific considerations:

| Language | Relevance | Notes |
|----------|-----------|-------|
| python | | |
| typescript | | |
| java | | |
| go | | |
| csharp | | |
| kotlin | | |
| rust | | |

---

## Quality Checklist

Before outputting, verify:
- [ ] Description is specific and actionable, not vague platitudes
- [ ] Rationale explains concrete harm (bugs, security issues, maintenance cost), not just "best practice"
- [ ] Violation message is terse and includes the pattern ID in parentheses
- [ ] Detection strategy explains the STRUCTURAL signal, not a behavioral one
- [ ] False positives are specific scenarios, not generic disclaimers
- [ ] References are real, authoritative URLs — not fabricated
- [ ] Tier/severity match the actual risk level (Tier 1 = security/reliability, Tier 3 = style/advisory)
```
