---
title: "Home"
---

# Sine

## Stop Architecture Drift Before It Happens

**Sine** enforces architectural decisions in code—not in Confluence docs that nobody reads.

While ESLint catches `var` vs `const`, Sine catches **"the UI is calling the database directly."**

---

## The Problem

Your team agrees on architectural patterns:
- ✓ "All HTTP calls must use circuit breakers"
- ✓ "No print statements in production code"
- ✓ "Use dependency injection for loose coupling"

**But how do you enforce these?**

Code reviews are manual, slow, and inconsistent. Documentation gets outdated. Linters can't detect high-level architecture violations.

---

## The Solution

Sine is an **Architectural Compliance Engine** that:

1. **Enforces patterns** as code—violations fail CI/CD
2. **Discovers patterns** already in your codebase automatically
3. **Works immediately** with 7 built-in architectural rules

Think of it as **ESLint for software architecture**.

---

## How It Works

```bash
# 1. Install (works immediately with built-in rules)
pip install sine

# 2. Check your codebase
sine check

# Output:
# ❌ src/api/client.py:23
#    HTTP call outside resilience wrapper (ARCH-001)
#
# ⚠️  src/utils/debug.py:15
#    Use logging instead of print() (ARCH-003)
```

---

## Built-In Rules

Sine ships with 7 curated rules that work out-of-box:

| Rule | What It Catches |
|------|-----------------|
| **[ARCH-001](/patterns/arch-001/)** | Unprotected HTTP calls (no circuit breaker) |
| **[ARCH-003](/patterns/arch-003/)** | Print statements in production code |
| **PATTERN-DISC-006** | Adapter pattern usage (for documentation) |
| **PATTERN-DISC-010** | Pipeline pattern implementations |
| **PATTERN-DISC-011** | Dependency injection examples |
| **PATTERN-DISC-012** | Context manager usage |
| **PATTERN-DISC-015** | Custom exception hierarchies |

[View full pattern catalog →](/patterns/)

---

## Key Differentiators

### vs. ESLint/Ruff
- **Sine**: Architectural decisions ("All HTTP needs resilience")
- **Them**: Code style ("Use const, not var")

### vs. ArchUnit
- **Sine**: Cross-language via Semgrep, with pattern discovery
- **ArchUnit**: Java-only, manual rule writing

### vs. Manual Code Review
- **Sine**: Automated, fast, consistent
- **Reviews**: Manual, slow, subjective

---

## Use Cases

### 1. Microservices Governance
Ensure services follow organizational patterns (health checks, circuit breakers, logging standards).

### 2. Legacy Modernization
Discover existing patterns before refactoring. Track adoption of new patterns over time.

### 3. Onboarding Documentation
Generate "How We Build Software" docs by analyzing actual code patterns.

### 4. Continuous Compliance
Block PRs that violate architectural decisions. No more "we agreed on this in the meeting."

---

## Quick Start

```bash
# Interactive setup
sine init

# Check your code
sine check

# Discover patterns
sine discover

# CI/CD integration (fails on violations)
sine check --format sarif
```

[Get Started →](/docs/)

---

## License

**Elastic License v2 (ELv2)**  
Free for internal use. Contact us for managed service licensing.
