# Sine

**Sine is not ESLint** - it's a next-generation code pattern enforcement and discovery tool.

Sine can be considered a "Architectural Compliance Engine" or even better, a "Governance-as-Code Platform (GaP) tool."
 * It enforces high-level architectural decisions (e.g., "All HTTP calls must use a circuit breaker") rather than low-level code style. It operates similarly to tools like ArchUnit or Open Policy Agent (OPA), but for code structure.
 * Key Differentiator: The "Discovery" aspect. Most tools only enforce known rules. sine proposes to learn what rules should exist, making it a "Knowledge-Driven Governance Tool".

## What is Sine?

Sine combines:
- **Pattern Enforcement**: Compile high-level coding guidelines into Semgrep rules and enforce them in your codebase
- **Pattern Discovery**: Use AI-powered research agents to discover best practices from trusted sources and generate enforcement rules automatically

## Features

### Core Enforcement Engine
- Load rule specifications from YAML files
- Compile specifications into Semgrep rules
- Run pattern matching across your codebase
- **Multiple Output Formats**: Text, JSON, and SARIF for CI/CD integration

### Governance Workflow
- **Pattern Discovery**: Use AI-powered agents to find patterns in your code
- **Promotion**: Transpile validated patterns into enforcement rules (`sine promote`)

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Check your codebase against defined patterns
sine check

# Discover new patterns for a topic
sine discover --topic "error handling"
```

## Project Status

Sine is in active development. It was extracted from the [ling](https://github.com/coreyt/ling) project to become a standalone tool.

## Documentation

- **[Configuration](docs/configuration.md)** - How to configure Sine via `pyproject.toml` or `sine.toml`.
- **`docs/research/`** - Design docs, pattern discovery methodology, validation results
- **`docs/specs/`** - Rule specifications, pattern library, and examples
  - `docs/specs/rule-specs/examples/` - 23 ready-to-use rule specs (3 ARCH, 20 PATTERN-DISC)
  - `docs/specs/pattern-library/` - Pattern examples and validation
  - `docs/specs/semgrep/` - Raw Semgrep query examples

## License

MIT
