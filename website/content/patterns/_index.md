---
title: "Pattern Catalog"
weight: 2
---

# Architectural Pattern Catalog

Sine's pattern catalog spans enforcement rules and discovery patterns.

## Enforcement Patterns (ARCH)

These **block violations** in CI/CD. Use them to enforce architectural decisions.

### [ARCH-001: HTTP Resilience](/patterns/arch-001/)
**Prevents**: Unprotected HTTP calls that cause cascading failures  
**Enforces**: Circuit breakers, retry logic, or resilience wrappers

### [ARCH-003: Logging Standards](/patterns/arch-003/)
**Prevents**: Print statements in production code  
**Enforces**: Structured logging or CLI-appropriate output (Click)

---

## Discovery Patterns (PATTERN-DISC)

These **document existing patterns** for analysis and architectural understanding.

### PATTERN-DISC-006: Adapter Pattern
**Detects**: Interface adaptation implementations  
**Use Case**: Document integration boundaries, API wrappers

### PATTERN-DISC-010: Pipeline Pattern
**Detects**: Sequential data transformation stages  
**Use Case**: ETL workflows, data processing chains

### PATTERN-DISC-011: Dependency Injection
**Detects**: Constructor injection, parameter injection  
**Use Case**: Assess testability, document service boundaries

### PATTERN-DISC-012: Context Managers
**Detects**: Resource management via `with` statements  
**Use Case**: Database connections, file handles, locks

### PATTERN-DISC-015: Exception Hierarchy
**Detects**: Custom exception class hierarchies  
**Use Case**: Error handling strategy documentation

---

## Custom Patterns

Create organization-specific rules:

```yaml
# .sine-rules/database-layer.yaml
schema_version: 1

rule:
  id: "ORG-DB-001"
  title: "Database calls through repository layer"
  description: "Direct db.execute() calls are forbidden"
  severity: "error"
  languages: [python]
  
  check:
    type: "forbidden"
    pattern: "db.execute(...)"
  
  reporting:
    default_message: "Use repository.query() instead"
```

[Learn how to write custom rules →](/docs/custom-rules/)

---

## Pattern Detection Tiers

| Tier | Engine | Speed | Capabilities |
|------|--------|-------|--------------|
| **Tier 1** | Semgrep (AST) | Fast | Pattern matching, structural search |
| **Tier 2** | Graph Analysis | Medium | Dependency paths, layering |
| **Tier 3** | CodeQL (Deep) | Slow | Taint analysis, control flow |

Most Sine rules use **Tier 1** for optimal performance.
