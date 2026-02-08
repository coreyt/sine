# Sine: Architectural Guideline Detection

**Status:** Design Phase
**Created:** 2026-02-05
**Author:** Claude + Human collaboration

---

## Executive Summary

**Sine** is a planned feature for ling that automates detection of architectural and design guideline violations—the "soft" rules that traditional linters cannot catch.

While linters handle the "first shift" (syntax, style, type safety), Sine handles structural correctness: dependency rules, required patterns, and engineering constraints that require understanding relationships between code blocks.

```
┌─────────────────────────────────────────────────────────────────┐
│  "First Shift" (Linters)        │  "Sine" (Architecture) │
│  ───────────────────────────────│──────────────────────────────  │
│  • Syntax correctness           │  • Structural correctness       │
│  • Style consistency            │  • Dependency rules             │
│  • Type safety                  │  • Pattern requirements         │
│  • Auto-fixable                 │  • Engineering judgment         │
│                                 │                                 │
│  ESLint, Ruff, Prettier, etc.   │  ling second-shift              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Problem Statement

### The Gap Between Linters and Code Review

Modern linters excel at detecting:
- Unused variables
- Type mismatches
- Formatting inconsistencies
- Common bug patterns

But they cannot detect:
- "HTTP calls must be wrapped in circuit breakers"
- "Data layer cannot import UI layer"
- "All services must implement health checks"
- "No circular dependencies between modules"

These rules require understanding **relationships** between code elements—not just individual nodes, but graphs of dependencies and call patterns.

### Current State

Teams document these rules in wikis or PDFs, then rely on:
1. **Code review** (inconsistent, doesn't scale)
2. **Tribal knowledge** (lost when people leave)
3. **Custom scripts** (unmaintained, fragile)

### Desired State

```bash
$ ling second-shift

Checking ARCH-001 (HTTP calls require circuit breakers)...
  ✗ src/api/client.py:45 - requests.get() outside circuit breaker

Checking ARCH-002 (No circular dependencies)...
  ✓ No cycles detected

Checking ARCH-003 (Data layer cannot import UI)...
  ✗ src/data/export.py:12 imports src/ui/formatters.py

2 violations found (1 baseline, 1 new)
Exit code: 1 (new violation detected)
```

---

## Architecture

### Core Principle: Orchestrator, Not Linter

ling Sine is a **Policy-as-Code orchestrator**, not another linter. It:

1. **Compiles** high-level guideline definitions into tool-specific rules
2. **Orchestrates** execution of detection engines
3. **Aggregates** results into a unified report mapped to your guidelines

This mirrors successful patterns like Terraform (HCL → Provider APIs) and Kubernetes (YAML → Container Runtime).

### System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Guidelines Definition                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │ High-Level DSL  │  │ Engine-Specific │  │ Documentation       │ │
│  │ (must_wrap,     │  │ (raw semgrep,   │  │ (human-readable     │ │
│  │  forbidden_path)│  │  raw codeql)    │  │  description)       │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘ │
└───────────┼─────────────────────┼─────────────────────┼────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌───────────────────────────────────────────────────────────────────┐
│                         ling compile                               │
│  • Translates high-level DSL → engine-specific rules              │
│  • Validates raw rules                                            │
│  • Generates documentation with "enforced by" sections            │
└───────────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                      ling second-shift                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Graph Engine │  │ Semgrep      │  │ External (CodeQL, etc.)  │ │
│  │ (built-in)   │  │ (subprocess) │  │ (opt-in, CI-only)        │ │
│  │              │  │              │  │                          │ │
│  │ • cycles     │  │ • AST pattern│  │ • deep data flow         │ │
│  │ • forbidden  │  │ • wrapper    │  │ • taint analysis         │ │
│  │ • layers     │  │   checks     │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│         ▲                 ▲                      ▲                 │
│         │                 │                      │                 │
│         └─────────────────┴──────────────────────┘                 │
│                    Tier 2 (Graph)  Tier 1 (AST)   Tier 3 (Deep)    │
└───────────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                        Unified Report                              │
│  • Violations mapped to guideline IDs (ARCH-001, etc.)            │
│  • Severity from tier (1/2/3)                                     │
│  • Location, snippet, suggested fix                               │
│  • Baseline comparison (known vs new)                             │
└───────────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                      Baseline Management                           │
│  • .ling-baseline.json stores known violations                    │
│  • New violations fail the build                                  │
│  • Known violations are collected but don't fail                  │
│  • `ling second-shift --update-baseline` to accept current state  │
└───────────────────────────────────────────────────────────────────┘
```

### Detection Tiers

| Tier | Detection Type | Engine | Complexity | Example |
|------|---------------|--------|------------|---------|
| **1** | AST Context (Wrapper) | Semgrep | Medium | "HTTP calls must be inside circuit breaker" |
| **2** | Dependency Graph (Topology) | Built-in | Low-Medium | "No circular imports", "Layer violations" |
| **3** | Control Flow (Reachability) | CodeQL | High | "No recursion in hot paths", "Taint tracking" |

**Key Insight:** Tier 2 (Graph) is where ling adds unique value. Semgrep handles Tier 1 well. CodeQL handles Tier 3 but is heavyweight. The dependency graph layer is poorly served by existing polyglot tools.

---

## Semgrep Role Analysis

### Primary for Tier 1, Secondary to Core Value

**Question:** Is Semgrep a primary or secondary tool for achieving Sine's goals?

**Answer:** **Both, depending on scope:**

1. **For Tier 1 (AST Pattern Matching):** Semgrep is **PRIMARY**
   - Required dependency for AST-based checks
   - Core engine for wrapper/context detection
   - No plan to build competing AST walker

2. **For Sine Overall:** Semgrep is **SECONDARY** to Tier 2
   - Tier 2 (Graph) is ling's unique value proposition
   - Semgrep is one component in a three-tier system
   - Built-in graph engine is the differentiation

3. **For ling as a Whole:** Semgrep is **ONE OF MANY TOOLS**
   - ling orchestrates multiple detection engines
   - Documentation generation remains core mission
   - Sine is a feature, not the product

### Why Semgrep? The Strategic Decision

**The Problem:** Detecting patterns like "HTTP calls must be inside circuit breakers" requires understanding AST context—what surrounds a particular code pattern.

**The Options:**

| Option | Effort | Maintainability | Language Support | Decision |
|--------|--------|-----------------|------------------|----------|
| Build custom AST walker | Very High | Poor (breaks often) | One at a time | ❌ Rejected |
| Use tree-sitter directly | High | Medium | Manual per language | ❌ Too complex |
| **Use Semgrep** | **Low** | **High** | **30+ languages** | **✅ Chosen** |
| Use CodeQL | Low | High | Limited, heavy | ⚠️ Tier 3 only |

**Key Benefits of Semgrep:**

1. **Mature & Proven**: Battle-tested in production environments
2. **Polyglot**: Supports Python, TypeScript, JavaScript, Java, C#, Go, Ruby, Rust, and 20+ more
3. **Tree-sitter Based**: Modern, fast parsing infrastructure
4. **Pattern Language**: Expressive syntax for AST matching (`pattern-not-inside`, `metavariable-pattern`, etc.)
5. **Active Development**: Backed by company (Semgrep/r2c), regular updates
6. **CI-Friendly**: Fast execution, designed for continuous integration

**The Design Decision (from Technical Risks section):**

> **Risk A: Universal AST Trap**
>
> **Risk:** Building a multi-language AST walker is a massive undertaking.
>
> **Mitigation:** Do not build one. Use Semgrep as the AST engine—it already uses tree-sitter and supports 30+ languages. ling compiles to Semgrep, not to AST traversals.

### The Orchestrator Pattern

ling does **NOT** compete with Semgrep. Instead, it **orchestrates** Semgrep as part of a multi-tier strategy:

```
User writes:              ling compiles to:           ling executes:
┌─────────────────┐      ┌──────────────────┐       ┌─────────────────┐
│ ling.yaml       │      │ Semgrep rules    │       │ semgrep CLI     │
│                 │  →   │ (temp config)    │   →   │ + parse output  │
│ High-level DSL  │      │                  │       │                 │
│ • must_wrap     │      │ patterns:        │       │ JSON results    │
│ • forbidden     │      │   - pattern: ... │       │                 │
│ • required_with │      │   - pattern-not  │       │                 │
└─────────────────┘      └──────────────────┘       └─────────────────┘
                                   ↓                          ↓
                         ┌──────────────────┐       ┌─────────────────┐
                         │ Graph algorithms │   →   │ Built-in engine │
                         │ (cycles, layers) │       │ + generate graph│
                         └──────────────────┘       └─────────────────┘
                                   ↓                          ↓
                         ┌──────────────────┐       ┌─────────────────┐
                         │ CodeQL queries   │   →   │ codeql CLI      │
                         │ (optional)       │       │ + parse SARIF   │
                         └──────────────────┘       └─────────────────┘
                                                             ↓
                                                    ┌─────────────────┐
                                                    │ Unified Report  │
                                                    │ (guideline IDs) │
                                                    └─────────────────┘
```

**This pattern mirrors:**
- **Terraform**: HCL → Provider APIs (AWS, Azure, GCP)
- **Kubernetes**: YAML → Container Runtime (Docker, containerd)
- **ESLint**: ESLint config → Parser plugins (Babel, TypeScript)

**Key principle:** High-level abstraction over specialized engines.

### Example: Compilation Flow

**User writes (high-level):**

```yaml
guidelines:
  - id: ARCH-001
    title: "HTTP calls require resilience patterns"
    check:
      type: must_wrap
      target: ["requests.get", "requests.post", "httpx.*"]
      wrapper: ["circuit_breaker", "@resilient", "with_retry"]
      languages: [python]
```

**ling compiles to (Semgrep-specific):**

```yaml
rules:
  - id: arch-001-impl
    languages: [python]
    severity: ERROR
    message: "HTTP call outside resilience pattern (ARCH-001)"
    patterns:
      - pattern-either:
          - pattern: requests.get(...)
          - pattern: requests.post(...)
          - pattern: httpx.$METHOD(...)
      - pattern-not-inside: |
          with circuit_breaker(...):
            ...
      - pattern-not-inside: |
          @resilient
          def $FUNC(...):
            ...
      - pattern-not-inside: |
          with with_retry(...):
            ...
```

**ling executes:**

```bash
# 1. Write compiled rules to temp file
/tmp/ling-second-shift-123.yaml

# 2. Run Semgrep
semgrep --config=/tmp/ling-second-shift-123.yaml \
        --json \
        --metrics=off \
        src/

# 3. Parse JSON output
# 4. Map results back to ARCH-001
# 5. Generate unified report
```

**Benefits of this approach:**
- ✅ Users don't need to know Semgrep pattern syntax
- ✅ Violation reports show "ARCH-001", not "arch-001-impl"
- ✅ Can swap engines without changing user-facing API
- ✅ Transparency: `--dry-run` shows compiled Semgrep rules

### Current State vs Future State

#### v1.0 (Current): Semgrep as Secondary Tool

In ling v1.0, Semgrep is **just one of 18 linters**:

| Ecosystem | Linters |
|-----------|---------|
| JavaScript/TypeScript | ESLint, TypeScript-ESLint, Prettier, TSConfig |
| Python | Ruff, Pyright |
| .NET | Roslyn, StyleCop |
| Java | Checkstyle, PMD, SpotBugs |
| C/C++ | Clang-Tidy, clang-format |
| Lua | Luacheck |
| Markdown | Markdownlint, PyMarkdown |
| **Multi-language** | **Semgrep, SonarQube** ← No special status |

**Role in v1.0:**
- Extract self-documenting rules from `.semgrep.yaml` configs
- Generate documentation for local Semgrep rules
- Store registry rule references (`p/ci`, `r/python.lang.security`)
- Treat as any other linter adapter

**Key characteristic:** Semgrep is **passive** - ling reads its config, doesn't execute it.

#### v2.0 (Sine): Semgrep as Primary Tier 1 Engine

In Sine, Semgrep becomes a **required external dependency**:

**Status Change:**

| Aspect | v1.0 | v2.0 (Sine) |
|--------|------|---------------------|
| Installation | Optional (if project uses Semgrep) | **Required** (for Tier 1 checks) |
| Execution | None (just read config) | **Active** (subprocess invocation) |
| Rule Generation | None | **Compile** high-level DSL to Semgrep rules |
| Criticality | One of many | **Core Tier 1 engine** |
| User Interaction | Users write `.semgrep.yaml` | Users write `ling.yaml`, ling generates Semgrep rules |

**New capabilities enabled by Semgrep:**
- Context-aware pattern matching ("X must be inside Y")
- Multi-language AST analysis without building custom parsers
- Wrapper/decorator detection
- Metavariable analysis (track data flow within function)

### What Semgrep Cannot Do (Why Tier 2 Exists)

Despite Semgrep's power, it **cannot** analyze cross-file relationships:

| Capability | Semgrep (Tier 1) | ling Graph Engine (Tier 2) |
|------------|------------------|---------------------------|
| **Pattern matching** | ✅ Excellent | ❌ Not designed for |
| **Wrapper detection** | ✅ `pattern-not-inside` | ❌ Not needed |
| **Circular dependencies** | ❌ Cannot detect | ✅ Graph algorithms |
| **Layer violations** | ❌ Single-file scope | ✅ Dependency analysis |
| **Forbidden paths** | ❌ No import tracking | ✅ Path finding |
| **Module topology** | ❌ No graph view | ✅ Core competency |

**Example: What Tier 2 detects that Semgrep cannot:**

```yaml
# Tier 2: Graph topology rules
check:
  type: topology
  rule: forbidden_paths
  forbidden:
    - from: "src/data/**"
      to: "src/ui/**"      # Data layer cannot import UI
    - from: "src/core/**"
      to: "src/plugins/**" # Core cannot depend on plugins
```

**Why Semgrep can't do this:**
- Semgrep analyzes individual files in isolation
- Cannot build import graph across entire codebase
- No concept of "module A imports module B"

**Why ling's Tier 2 can:**
- Parses all import statements (Python, TypeScript, C#)
- Builds directed graph of dependencies
- Runs graph algorithms (cycle detection, path finding, topological sort)
- **This is ling's unique value proposition**

### Comparison with Alternatives

#### Why Not Just Use Semgrep Directly?

**User could write Semgrep rules themselves. Why use ling?**

**Reasons:**

1. **Higher-Level DSL**: `must_wrap` is clearer than Semgrep patterns
   ```yaml
   # ling DSL (user-friendly)
   type: must_wrap
   target: ["requests.*"]
   wrapper: ["circuit_breaker"]

   # vs Semgrep (expert-level)
   patterns:
     - pattern: requests.$METHOD(...)
     - pattern-not-inside: |
         with circuit_breaker(...):
           ...
   ```

2. **Unified Multi-Tier**: Combines AST (Semgrep) + Graph (built-in) + CodeQL (opt-in)
   - Single tool, single report format
   - User doesn't need to learn three different tools
   - Results all map to guideline IDs

3. **Documentation Integration**: Guidelines are documented in coding standards
   - `ling build` includes Sine results
   - Violations shown in generated docs
   - Single source of truth

4. **Baseline Management**: Built-in handling of known violations
   - `.ling-baseline.json` auto-managed
   - Only new violations fail CI
   - Gradual adoption for legacy codebases

5. **Escape Hatch**: `type: raw` for complex Semgrep rules
   - Full access to Semgrep features when needed
   - Best of both worlds

#### Why Not Armada or Other Graph Tools?

**Comparison with Armada (from graph-ir-ecosystem):**

| | ling Sine | Armada |
|---|---|---|
| **Philosophy** | Lightweight, CI-friendly | Comprehensive, accurate |
| **Speed Target** | < 30 seconds | Slower, thorough |
| **Accuracy** | 80% (regex imports OK) | High (full AST indexing) |
| **Infrastructure** | Zero deps (Tier 2) | Memgraph + Qdrant |
| **Use Case** | Quick CI checks | Deep codebase analysis |
| **Parsing Depth** | Imports only | Full semantic analysis |

**Different tools for different needs:**
- **Use ling Sine**: CI enforcement, coding guidelines, fast feedback
- **Use Armada**: Architecture documentation, large codebase exploration, semantic queries

**They're complementary**, not competitive. (See [graph-ir-ecosystem-alignment.md](./graph-ir-ecosystem-alignment.md) for full analysis.)

### Strategic Implications

#### Installation & Deployment

**Semgrep as External Dependency:**

```toml
# pyproject.toml
[project.dependencies]
# ... existing deps ...

[project.optional-dependencies]
second-shift = [
    "semgrep>=1.50.0,<2.0.0",  # Required for Tier 1
]
```

**Installation:**
```bash
pip install ling[second-shift]
```

**Verification:**
```bash
$ ling second-shift --check-deps
Checking dependencies...
  ✓ semgrep 1.55.0 (required: >=1.50.0)
  ✓ Python 3.10.0 (required: >=3.10)

Ready to run Sine checks.
```

#### Version Compatibility

**Strategy:** Pin to minor version range, test against multiple versions.

```yaml
# .github/workflows/test-second-shift.yml
matrix:
  semgrep-version: ["1.50.0", "1.55.0", "1.60.0"]
```

**Risk:** Semgrep changes CLI interface or output format.

**Mitigation:**
- Integration tests against real Semgrep
- Parse JSON output (stable contract)
- Fallback to text parsing if JSON changes
- Version warnings if unsupported Semgrep detected

#### Transparency & Trust

**User Concern:** "What is ling doing with my code?"

**Answer:** Full transparency with `--dry-run`:

```bash
$ ling second-shift --dry-run

Compiling guidelines to detection rules...

[Tier 1: Semgrep Rules]
Would write to: /tmp/ling-second-shift-abc123.yaml

---
rules:
  - id: arch-001-impl
    languages: [python]
    message: "HTTP call outside circuit breaker (ARCH-001)"
    patterns:
      - pattern: requests.$METHOD(...)
      - pattern-not-inside: |
          with circuit_breaker(...):
            ...
---

Would execute:
  semgrep --config=/tmp/ling-second-shift-abc123.yaml \
          --json --metrics=off src/

[Tier 2: Graph Analysis]
Would run built-in checks:
  - Circular dependency detection
  - Forbidden path analysis: src/data/** → src/ui/**

[Tier 3: CodeQL]
Skipped (opt-in only, use --deep flag)
```

**This shows:**
- ✅ Exact Semgrep rules that would run
- ✅ Command-line invocation
- ✅ What data is analyzed
- ✅ No hidden behavior

#### Escape Hatch: Direct Semgrep Access

**For complex rules, use `type: raw`:**

```yaml
guidelines:
  - id: ARCH-005
    title: "No SQL injection"
    check:
      type: raw
      engine: semgrep
      config: |
        rules:
          - id: arch-005-impl
            patterns:
              - pattern-either:
                  - pattern: execute("SELECT ... " + $VAR)
                  - pattern: cursor.execute(f"SELECT {$VAR}")
              - metavariable-pattern:
                  metavariable: $VAR
                  pattern: request.$FIELD
            message: "Possible SQL injection"
            languages: [python]
            severity: ERROR
```

**This gives:**
- Full access to Semgrep's advanced features
- No compilation/translation (direct pass-through)
- Still unified reporting (maps to ARCH-005)

### Risks & Mitigations

#### Risk: Semgrep Installation Friction

**Problem:** Users must install Semgrep separately.

**Mitigation:**
1. **Clear documentation**: Installation guide in README
2. **Helpful error messages**:
   ```
   Error: semgrep not found

   Sine requires Semgrep for Tier 1 checks.

   Install options:
     • pip install ling[second-shift]
     • brew install semgrep
     • See: https://semgrep.dev/docs/getting-started/
   ```
3. **Graceful degradation**: If Semgrep not found, skip Tier 1 (run Tier 2 only)
4. **CI templates**: Provide GitHub Actions / GitLab CI examples

#### Risk: Semgrep API Changes

**Problem:** Semgrep could change CLI interface, breaking integration.

**Mitigation:**
1. **JSON output**: More stable than text output
2. **Version detection**: Warn if unsupported version
3. **Integration tests**: Run against real Semgrep in CI
4. **Fallback parsing**: Multiple strategies for output parsing
5. **Version pinning**: Document tested versions

#### Risk: Performance / Rate Limiting

**Problem:** Semgrep might be slow on large codebases.

**Mitigation:**
1. **Incremental analysis**: Only analyze changed files (future)
2. **Caching**: Cache Semgrep results per commit hash
3. **Tier isolation**: User can run Tier 2 only if Tier 1 is slow
4. **Parallel execution**: Run Semgrep and graph analysis concurrently

#### Risk: False Positives

**Problem:** Semgrep rules might have high false positive rate.

**Mitigation:**
1. **Baseline system**: Known violations don't fail CI
2. **Ignore comments**: `# ling: ignore ARCH-001` support
3. **Iterative refinement**: Start with high-precision rules
4. **User control**: `type: raw` for fine-tuning
5. **Confidence levels**: Report certainty of violations

### Success Criteria for Semgrep Integration

**Phase 1a complete when:**
- [x] Decision documented (this section)
- [ ] DSL-to-Semgrep compiler implemented
- [ ] Subprocess execution working
- [ ] JSON parsing robust
- [ ] Result mapping to guideline IDs
- [ ] `--dry-run` shows compiled rules
- [ ] Integration tests against real Semgrep
- [ ] At least 3 check types compile correctly (`must_wrap`, `forbidden`, `required_with`)

**Production ready when:**
- [ ] Tested with Semgrep 1.50.0 - 1.60.0
- [ ] Documentation complete
- [ ] CI examples provided
- [ ] Error messages helpful
- [ ] False positive rate < 10% on real projects
- [ ] Performance acceptable (< 30s for medium projects)

---

## Schema Specification

### Guideline Definition Structure

```yaml
# In ling.yaml or best-practices/*.yaml
guidelines:
  - id: ARCH-001                    # Unique identifier
    title: "HTTP calls require resilience patterns"
    description: |
      All outbound HTTP calls must be wrapped in circuit breakers
      or retry logic to prevent cascade failures.
    tier: 1                         # Enforcement tier (1=mandatory, 2=recommended, 3=contextual)
    category: "resilience"

    # Detection specification
    check:
      type: must_wrap               # High-level DSL type
      target:                       # What we're looking for
        - "requests.get"
        - "requests.post"
        - "httpx.get"
        - "fetch"
      wrapper:                      # Required context
        - "circuit_breaker"
        - "with_retry"
        - "@resilient"
      languages: [python, typescript]
```

### Check Types (High-Level DSL)

#### Type: `must_wrap`
Pattern must appear inside a wrapper context.

```yaml
check:
  type: must_wrap
  target: ["requests.*", "http.get"]
  wrapper: ["circuit_breaker", "@Retry"]
  languages: [python]
```

Compiles to Semgrep:
```yaml
patterns:
  - pattern: requests.$METHOD(...)
  - pattern-not-inside: |
      with circuit_breaker(...):
        ...
```

#### Type: `forbidden`
Pattern must not appear.

```yaml
check:
  type: forbidden
  pattern: "eval($X)"
  languages: [python, javascript]
  message: "eval() is forbidden due to security risks"
```

#### Type: `required_with`
If pattern A exists, pattern B must also exist.

```yaml
check:
  type: required_with
  if_present: "@Service"
  must_have: "@HealthCheck"
  scope: class
  languages: [java, csharp]
```

#### Type: `topology`
Dependency graph rules (built-in engine).

```yaml
check:
  type: topology
  rule: no_cycles              # or: forbidden_paths, layers
  scope: "src/**"
```

```yaml
check:
  type: topology
  rule: forbidden_paths
  forbidden:
    - from: "src/data/**"
      to: "src/ui/**"
    - from: "src/core/**"
      to: "src/plugins/**"
```

```yaml
check:
  type: topology
  rule: layers
  layers:                      # Ordered top to bottom
    - "src/ui/**"              # Can import: data, core
    - "src/data/**"            # Can import: core
    - "src/core/**"            # Can import: nothing above
```

#### Type: `raw`
Escape hatch for complex rules—embed engine-specific configuration directly.

```yaml
check:
  type: raw
  engine: semgrep
  config: |
    rules:
      - id: arch-001-impl
        patterns:
          - pattern-either:
              - pattern: $SINK($USER_INPUT)
          - metavariable-pattern:
              metavariable: $USER_INPUT
              pattern: request.params.$KEY
        message: "Unsanitized user input reaches sink"
```

### Baseline File Structure

```json
// .ling-baseline.json
{
  "version": 1,
  "created": "2026-02-05T10:30:00Z",
  "updated": "2026-02-05T14:22:00Z",
  "violations": [
    {
      "guideline_id": "ARCH-001",
      "file": "src/api/legacy_client.py",
      "line": 45,
      "hash": "a1b2c3d4",  // Hash of violation context for stability
      "reason": "Legacy code, scheduled for refactor in Q2"
    },
    {
      "guideline_id": "ARCH-003",
      "file": "src/data/export.py",
      "line": 12,
      "hash": "e5f6g7h8",
      "reason": null
    }
  ]
}
```

---

## Implementation Phases

### Phase 0: Schema & Compilation (Foundation)

**Goal:** Prove the model without executing any checks.

**Deliverables:**
1. Schema definition for guidelines with `check` field
2. `ling second-shift --dry-run` that validates and shows what would run
3. Documentation generation that includes "Enforced by: [engine]" sections
4. Baseline file format specification

**Exit Criteria:**
- Can define guidelines with checks in YAML
- `--dry-run` shows compiled Semgrep rules
- Generated docs show enforcement method

### Phase 1a: Semgrep Orchestration (Tier 1)

**Goal:** Execute AST-based checks via Semgrep.

**Deliverables:**
1. Compile high-level DSL (`must_wrap`, `forbidden`) to Semgrep rules
2. Execute Semgrep as subprocess
3. Parse Semgrep JSON output
4. Map results back to guideline IDs
5. Unified report format

**Languages:** Python, TypeScript, C# (Semgrep supports all)

**Exit Criteria:**
- `ling second-shift` runs Semgrep checks
- Violations show guideline ID, not Semgrep rule ID
- Report includes file, line, snippet

### Phase 1b: Graph Engine (Tier 2)

**Goal:** Built-in dependency graph analysis.

**Deliverables:**
1. Import parser for Python (regex-based, ~80% accuracy)
2. Directed graph construction
3. Cycle detection algorithm
4. Forbidden path checking
5. Layer violation detection

**Languages:** Python first

**Exit Criteria:**
- `no_cycles` rule detects circular imports
- `forbidden_paths` rule detects layer violations
- Works without external dependencies

### Phase 2: Graph Engine Expansion

**Goal:** Extend graph engine to more languages.

**Deliverables:**
1. TypeScript import parser (handles `tsconfig.json` paths)
2. C# using/namespace parser
3. Unified graph representation

**Languages:** TypeScript, C#

**Exit Criteria:**
- Same topology rules work across all three languages
- Path resolution handles each language's module system

### Phase 3: Baseline Management

**Goal:** Production-ready violation management.

**Deliverables:**
1. Baseline file read/write
2. Violation hashing (stable across minor code changes)
3. `--update-baseline` command
4. New vs known violation differentiation
5. Exit codes: 0 (clean), 1 (new violations), 2 (config error)

**Exit Criteria:**
- Existing codebase can establish baseline
- Only new violations fail CI
- Baseline can be committed to repo

### Phase 4: Deep Integration (Tier 3, Optional)

**Goal:** CodeQL integration for complex analysis.

**Deliverables:**
1. CodeQL orchestration (if installed)
2. Raw CodeQL query support in schema
3. Result mapping to guidelines

**Exit Criteria:**
- `type: raw, engine: codeql` works
- Opt-in via `--deep` flag or config

### Phase 5: Build Integration

**Goal:** Integrate into main ling workflow.

**Deliverables:**
1. `ling build --check-guidelines` flag
2. Run second-shift before generating docs
3. Include violation summary in generated docs
4. Consider: block doc generation on new violations?

**Exit Criteria:**
- Single command for full workflow
- Docs reflect current compliance state

---

## Technical Risks & Mitigations

### Risk A: Universal AST Trap

**Risk:** Building a multi-language AST walker is a massive undertaking.

**Mitigation:** Do not build one. Use Semgrep as the AST engine—it already uses tree-sitter and supports 30+ languages. ling compiles to Semgrep, not to AST traversals.

### Risk B: Import Resolution Swamp

**Risk:** Resolving imports correctly requires understanding `PYTHONPATH`, `tsconfig.json` paths, Java classpaths, etc.

**Mitigation:**
- Start with static regex-based parsing (handles 80% of cases)
- Accept imperfection—document that dynamic imports are unsupported
- For TypeScript, read `tsconfig.json` paths; for Python, use simple heuristics

### Risk C: Toolchain Bloat

**Risk:** Requiring Semgrep + CodeQL + other tools creates deployment friction.

**Mitigation:**
- Tier 1 (Semgrep): Required for AST checks, but it's a single binary
- Tier 2 (Graph): Built-in, no external deps
- Tier 3 (CodeQL): Opt-in, CI-only, clearly documented as optional

### Risk D: False Positive Fatigue

**Risk:** Too many false positives leads to developers ignoring the tool.

**Mitigation:**
- Baseline system (ignore known violations)
- `# ling: ignore ARCH-001` comment support
- Confidence levels in reports
- Start with high-precision rules, add more over time

### Risk E: CI Performance Wall

**Risk:** Slow checks won't be run on every PR.

**Mitigation:**
- Tier 2 (Graph) is fast—just parsing and graph algorithms
- Tier 1 (Semgrep) is reasonably fast
- Tier 3 (CodeQL) is opt-in for nightly/weekly runs
- Future: incremental checking (only changed files)

### Risk F: Schema Magic

**Risk:** High-level DSL hides too much, becomes unpredictable.

**Mitigation:**
- `--dry-run` shows exactly what will be executed
- `type: raw` escape hatch for full control
- Clear documentation of what each DSL type compiles to

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-06 | Added comprehensive Semgrep role analysis | Documents strategic choice: Semgrep as primary Tier 1 engine, secondary to Tier 2 graph analysis core value; includes orchestrator pattern, comparison with alternatives, risks/mitigations |
| 2026-02-05 | Feature named "Sine" | Implies second pass after linting |
| 2026-02-05 | Baseline file strategy | Collect all violations, ignore known, fail on new |
| 2026-02-05 | Semgrep as Tier 1 engine | Proven polyglot AST analysis, avoids building our own |
| 2026-02-05 | Built-in graph engine for Tier 2 | Unique value-add, lightweight, no good polyglot alternative |
| 2026-02-05 | Language priority: Python → TypeScript → C# | Complexity order, covers major ecosystems |
| 2026-02-05 | Start as separate command | `ling second-shift`, integrate to build later |
| 2026-02-05 | Accept import resolution imperfection | 80% accuracy with regex is acceptable for v1 |

---

## Graph Export Format

**Purpose**: Enable integration with graph visualization and code understanding tools.

**Supported Format**: [Graph-IR](https://github.com/coreyt/graph-ir) - JSON-based directed acyclic graph representation.

**Usage**:
```bash
ling second-shift --export-format=graph-ir > deps.json
```

**Integration Opportunities**:
- **Coral** (graph-ir-tools ecosystem): Visualize dependency graphs and violations
- **Armada** (graph-ir-tools ecosystem): Combine lightweight dependency analysis with deep code understanding
- **Third-party tools**: Any tool that supports Graph-IR import

**Node Types**:
- `module`: Python module, TypeScript file, C# namespace
- `package`: Python package, npm package, NuGet package

**Edge Types**:
- `imports`: Direct import relationship
- `depends_on`: Dependency (more general)
- `violates`: Architecture rule violation
- `circular`: Circular dependency

**Metadata**:
- `notation: "ling-dependency-graph"`
- Guideline violations count
- Language and timestamp

See [graph-ir-ecosystem-alignment.md](./graph-ir-ecosystem-alignment.md) for detailed integration strategy with the Graph-IR ecosystem.

---

## Open Questions (For Future Resolution)

1. **Ignore comment syntax:** `# ling: ignore ARCH-001` or `# second-shift: ignore ARCH-001`?

2. **Baseline scope:** Per-file baselines or single project baseline?

3. **Semgrep installation:** Require user to install, or bundle/download automatically?

4. **Report formats:** Text, JSON, SARIF (for GitHub integration), Graph-IR?

5. **Configuration location:** In `ling.yaml` under `second_shift:` or separate file?

6. **Graph granularity:** File-level, module-level, or class-level dependency graphs?

---

## Success Criteria

### Phase 1 Complete When:
- [ ] `ling second-shift` runs on a Python project
- [ ] At least 3 check types work (`must_wrap`, `forbidden`, `topology/no_cycles`)
- [ ] Violations map to guideline IDs in report
- [ ] Baseline file can be created and used

### Production Ready When:
- [ ] Works for Python, TypeScript, and C#
- [ ] CI integration documented
- [ ] False positive rate < 10%
- [ ] Execution time < 30 seconds for medium projects
- [ ] At least 3 real-world projects using it

---

## References

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [ArchUnit (Java)](https://www.archunit.org/)
- [Dependency-Cruiser (JS)](https://github.com/sverweij/dependency-cruiser)
- [CodeQL](https://codeql.github.com/)
- [ling v2 Roadmap: Engineering Risk Management](./roadmap-version-2.md)
