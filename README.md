# Sine

**Sine is not ESLint** - it's a next-generation code pattern enforcement and discovery tool.

## What is Sine?

Sine combines:
- **Pattern Enforcement**: Compile high-level coding guidelines into Semgrep rules and enforce them in your codebase
- **Pattern Discovery**: Use AI-powered research agents to discover best practices from trusted sources and generate enforcement rules automatically

## Features

### Core Enforcement Engine
- Load rule specifications from YAML files
- Compile specifications into Semgrep rules
- Run pattern matching across your codebase
- Maintain a baseline of known findings
- Report on new violations

### Pattern Discovery
- Research architecture patterns using web search and LLM extraction
- Discover implementation patterns from trusted documentation
- Validate patterns against credibility sources
- Generate rule specifications automatically

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

- **`docs/research/`** - Design docs, pattern discovery methodology, validation results
- **`docs/specs/`** - Rule specifications, pattern library, and examples
  - `docs/specs/rule-specs/examples/` - 23 ready-to-use rule specs (3 ARCH, 20 PATTERN-DISC)
  - `docs/specs/pattern-library/` - Pattern examples and validation
  - `docs/specs/semgrep/` - Raw Semgrep query examples

## License

MIT
