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

### Built-In Rules (ESLint-style)
- **7 curated architectural rules** shipped with the package
- Works out-of-box without setup
- Covers resilience patterns, code quality, and architectural patterns
- Customizable: override or extend with local rules

### Core Enforcement Engine
- Load rule specifications from YAML files
- Compile specifications into Semgrep rules
- Run pattern matching across your codebase
- **Multiple Output Formats**: Text, JSON, and SARIF for CI/CD integration

### Governance Workflow
- **Interactive Setup**: `sine init` command for easy onboarding
- **Pattern Discovery**: Use AI-powered agents to find patterns in your code
- **Promotion**: Transpile validated patterns into enforcement rules (`sine promote`)

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Initialize Sine for your project (interactive setup)
sine init

# Or just start checking with built-in rules
sine check

# Discover patterns in your codebase
sine discover
```

Sine works immediately without configuration - it ships with 7 built-in architectural rules. The `init` command helps you customize settings and optionally add project-specific rules.

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

This project is licensed under the **Elastic License v2 (ELv2)**.

We chose this license because we believe in building in the open, but we also believe in protecting the hard work our team has put into this project from being "strip-mined" by large cloud providers.

#### What this means for you:

* **Individuals & Companies:** You can use, modify, and redistribute the code for free for almost any internal or commercial use.
* **Modifications:** You are free to modify the code to suit your or your customer's needs without being forced to open-source your proprietary changes (no "viral" copyleft).
* **Contributions:** We welcome pull requests! (Note: contributions may require a simple CLA).

#### What you cannot do:

* **Managed Services:** You cannot provide this software as a managed service (SaaS) to third parties. If you are a hyperscaler or service provider looking to sell "Sine-as-a-Service," you must contact us for a commercial license.
* **No Circumvention:** You cannot bypass any license key or security features built into the software.
* **No Sublicensing:** You cannot sell the license to others or claim the code as your own.

> **In short:** If you aren't trying to build a competing AWS-style managed service using our code, you are likely good to go.

