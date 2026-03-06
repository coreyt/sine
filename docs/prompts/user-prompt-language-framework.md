# User Prompt: Language-Framework Variant Specification

> **Usage**: After language-generic variants are reviewed, send this prompt to generate framework-specific variants. Only create framework variants where the generic pattern is genuinely insufficient.

```
## Task

Generate the **Framework Variant** (Section 3) for the following pattern, language, and framework.

### Approved Top-Level Specification

{{TOP_LEVEL_SPEC}}

### Approved Language-Generic Variant

{{LANGUAGE_GENERIC_SPEC}}

### Target Framework

**Language**: {{LANGUAGE}}
**Framework**: {{FRAMEWORK}}
**Framework version constraint**: {{FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP}}

## Instructions

1. **Justify the variant first.** Explain WHY the generic {{LANGUAGE}} pattern is insufficient for {{FRAMEWORK}}. If the generic pattern already works well for this framework, output ONLY:
   ```
   SKIP: The generic {{LANGUAGE}} variant adequately covers {{FRAMEWORK}} usage.
   Reason: [brief explanation]
   ```
   Do NOT create a framework variant just to have one.

2. If a variant IS justified, research:
   - {{FRAMEWORK}}'s specific base classes, decorators, annotations, or conventions that affect detection
   - {{FRAMEWORK}}'s built-in mechanisms for this pattern (e.g., Angular DI, Spring IoC, Django ORM)
   - {{FRAMEWORK}} documentation and migration guides for relevant versions
   - How the generic pattern would produce false positives or miss framework-idiomatic violations

3. Write a Semgrep rule that detects framework-specific violations:
   - Reference framework base classes, decorators, annotations directly
   - Rule ID: `{{PATTERN_ID_LOWER}}-{{LANGUAGE}}-{{FRAMEWORK}}-impl`
   - The framework variant should be MORE SPECIFIC than the generic (fewer false positives), not broader

4. Provide realistic good and bad code examples using {{FRAMEWORK}} idioms (3-12 lines each).

## Output Format

---

### Framework: `{{FRAMEWORK}}` (Language: `{{LANGUAGE}}`)

| Field | Value |
|-------|-------|
| **Framework name** | `{{FRAMEWORK}}` |
| **Version constraint** | `{{FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP}}` |

**Why a separate variant?**
> [Specific framework idiom that makes the generic pattern insufficient]

**Check type**: _(`forbidden`, `must_wrap`, `required_with`, `raw`, or `pattern_discovery`)_

**Semgrep pattern(s)**:
```yaml
[If raw, provide complete rule YAML]
[If forbidden/must_wrap/etc., provide just the pattern string]
```

**Good example** (framework-idiomatic code that follows the pattern):
```{{LANGUAGE}}
[3-12 lines showing proper framework usage]
```

**Bad example** (framework code that violates the pattern):
```{{LANGUAGE}}
[3-12 lines showing violation in framework context]
```

**Framework-specific notes:**
> [Framework conventions, migration notes, documentation references]

---

## Common Language-Framework Combinations

For reference, these are the most common frameworks per language:

| Language | Frameworks |
|----------|-----------|
| python | django, flask, fastapi, sqlalchemy, celery, pytest |
| typescript | angular, react, nestjs, express, prisma, next |
| java | spring, jakarta-ee, hibernate, micronaut, quarkus |
| go | gin, echo, fiber, gorm, chi |
| csharp | aspnet-core, efcore, blazor, maui |
| kotlin | spring-boot, ktor, exposed, compose |
| ruby | rails, sinatra, dry-rb, rspec |
| rust | actix, axum, tokio, diesel, rocket |

Only generate variants for frameworks where the detection genuinely differs.

## Quality Checklist

Before outputting, verify:
- [ ] Variant is JUSTIFIED — the generic pattern genuinely doesn't work for this framework
- [ ] Pattern references actual framework classes/decorators/annotations (not made-up names)
- [ ] Rule ID follows: `{{PATTERN_ID_LOWER}}-{{LANGUAGE}}-{{FRAMEWORK}}-impl`
- [ ] Framework variant is MORE SPECIFIC than generic (narrower match, fewer false positives)
- [ ] Good example uses framework idioms correctly
- [ ] Bad example shows a realistic framework-specific violation
- [ ] Version constraint matches when the relevant framework feature was introduced
- [ ] Framework-specific notes reference official documentation
```
