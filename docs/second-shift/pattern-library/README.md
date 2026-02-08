# Sine Pattern Library

This directory contains Semgrep rules for discovering design patterns in codebases.

## Purpose

Pattern discovery rules identify **where patterns are being used** (descriptive), as opposed to enforcement rules that find **where patterns are violated** (prescriptive).

## Files

- **`examples.yaml`** - Comprehensive collection of 20+ pattern discovery rules
  - Creational patterns (Singleton, Factory, Builder)
  - Structural patterns (Adapter, Registry, Decorator)
  - Behavioral patterns (Observer, Strategy, Template Method, Command)
  - Architectural patterns (Pipeline, Dependency Injection, Context Manager)
  - Python-specific patterns (Pydantic, frozen dataclass, Protocol, Enum)
  - Error handling patterns (Exception hierarchy, Result types)
  - Type patterns (Type guards, Protocols)

## Usage

### Testing Pattern Discovery

Run pattern discovery on a codebase:

```bash
semgrep --config=docs/second-shift/pattern-library/examples.yaml src/ --metrics=off
```

### Integration with Sine (Future)

Once implemented in Sine:

```bash
# Discover all patterns
ling second-shift --discover-patterns

# Discover specific patterns
ling second-shift --discover-patterns=creational,structural

# Export to documentation
ling second-shift --discover-patterns --export-markdown=docs/patterns-in-use.md
```

## Pattern Categories

### Creational Patterns
Design patterns for object creation mechanisms.

- **Singleton** - Ensures a class has only one instance
- **Factory** - Encapsulates object creation logic
- **Builder** - Constructs complex objects step by step

### Structural Patterns
Design patterns for composing classes and objects.

- **Adapter** - Converts interface of a class into another interface
- **Registry** - Centralized storage for instances indexed by key
- **Decorator** - Adds responsibilities to objects dynamically
- **Immutable Data** - Prevents accidental mutation (Python: frozen dataclass)

### Behavioral Patterns
Design patterns for communication between objects.

- **Observer** - Notifies multiple objects of state changes
- **Strategy** - Encapsulates interchangeable algorithms
- **Template Method** - Defines skeleton with steps in subclasses
- **Command** - Encapsulates requests as objects

### Architectural Patterns
Higher-level structural patterns for application architecture.

- **Pipeline** - Sequential processing stages
- **Dependency Injection** - Dependencies passed via constructor
- **Context Manager** - Resource management with automatic cleanup

### Python-Specific Patterns
Patterns that leverage Python-specific features.

- **Pydantic Validation** - Runtime data validation
- **Protocol** - Structural typing interfaces
- **Enum** - Type-safe constants
- **Decorator Functions** - Function wrappers for cross-cutting concerns

### Error Handling Patterns
Patterns for error management.

- **Exception Hierarchy** - Custom exception types for domain errors
- **Result Type** - Explicit success/failure handling

## Adding New Patterns

When adding a new pattern definition:

1. **Choose the right category** (creational, structural, behavioral, etc.)
2. **Write clear patterns** that match the AST structure
3. **Set appropriate confidence** (HIGH, MEDIUM, LOW)
4. **Add metadata** for context
5. **Test on real code** to verify accuracy

### Example Pattern Definition

```yaml
rules:
  - id: detect-pattern-name
    message: "Clear description of what this pattern is"
    severity: INFO  # Always INFO for discovery
    languages: [python]
    patterns:
      - pattern: |
          # Your Semgrep pattern here
      - metavariable-pattern:
          metavariable: $VAR
          pattern-regex: NameConvention.*
    metadata:
      pattern_type: pattern_name
      category: creational  # or structural, behavioral, etc.
      confidence: HIGH  # or MEDIUM, LOW
      description: "Short description of the pattern"
      note: "Optional context about when this pattern is used"
```

## Validation

All patterns in this library have been validated against the ling codebase:

- **Total patterns:** 20+
- **Tested on:** ling src/ling/ (80 files)
- **Validation results:** See [validation document](../../research/second-shift-pattern-discovery-validation.md)

## Future Enhancements

- [ ] Language-specific libraries (TypeScript, Java, C#, Go)
- [ ] Pattern quality metrics
- [ ] Anti-pattern detection
- [ ] Pattern relationship mapping
- [ ] Community-contributed patterns

## References

- [Pattern Discovery Design Document](../../research/second-shift-pattern-discovery.md)
- [Validation Results](../../research/second-shift-pattern-discovery-validation.md)
- [Sine Design](../../research/second-shift-design.md)
- [Semgrep Pattern Syntax](https://semgrep.dev/docs/writing-rules/pattern-syntax/)
