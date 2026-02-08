# Sine Rule Specification Schema

This directory contains architectural guideline rule specifications for Sine.

## File Format

Rule specifications are YAML files with the following structure:

```yaml
schema_version: 1

rule:
  id: "ARCH-001"                    # Unique identifier (required)
  title: "Short descriptive title"  # Human-readable title (required)
  description: |                     # Detailed description (required)
    Multi-line description of what this rule checks.
  rationale: |                       # Why this rule exists (required)
    Explanation of the reasoning behind this rule.
  tier: 1                            # 1=Tier 1 (Semgrep), 2=Tier 2 (Graph), 3=Tier 3 (Deep) (required)
  category: "category-name"          # E.g., "security", "resilience", "operations" (required)
  severity: "error"                  # "error", "warning", or "info" (required)
  languages: [python]                # Supported languages (required)

  check:                             # Detection specification (required)
    type: "must_wrap"                # Check type - see below (required)
    # ... type-specific fields

  reporting:                         # How violations are reported (required)
    default_message: "Violation message"  # Message shown to users (required)
    confidence: "high"               # "low", "medium", or "high" (required)
    documentation_url: null          # Optional URL for more info

  examples:                          # Code examples (required)
    good:                            # Examples of compliant code
      - language: python
        code: |
          # Compliant code example
    bad:                             # Examples of violations
      - language: python
        code: |
          # Non-compliant code example

  references:                        # External references (required, can be empty list)
    - "https://example.com/architecture/guidelines"
```

## Check Types

### Type: `must_wrap`

Requires that a target pattern appears only inside a wrapper context.

**Fields:**
- `type`: `"must_wrap"` (required)
- `target`: List of patterns to find (required)
- `wrapper`: List of required wrapper contexts (required)

**Example:**
```yaml
check:
  type: "must_wrap"
  target:
    - "requests.get"
    - "requests.post"
  wrapper:
    - "circuit_breaker"      # with circuit_breaker(...):
    - "@resilient"           # Decorator
```

### Type: `forbidden`

Prohibits a specific pattern from appearing.

**Fields:**
- `type`: `"forbidden"` (required)
- `pattern`: Semgrep pattern to forbid (required)

**Example:**
```yaml
check:
  type: "forbidden"
  pattern: "eval($X)"
```

### Type: `required_with`

If pattern A exists, pattern B must also exist.

**Fields:**
- `type`: `"required_with"` (required)
- `if_present`: Pattern to check for (required)
- `must_have`: Required accompanying pattern (required)
- `scope`: `"function"` or `"class"` (optional)

**Example:**
```yaml
check:
  type: "required_with"
  if_present: "@service"
  must_have: "@health_check"
  scope: "function"
```

### Type: `raw`

For complex rules that require direct Semgrep configuration.

**Fields:**
- `type`: `"raw"` (required)
- `engine`: `"semgrep"` (required)
- `config`: Inline Semgrep YAML configuration (required)

**Example:**
```yaml
check:
  type: "raw"
  engine: "semgrep"
  config: |
    rules:
      - id: arch-001-impl
        patterns:
          - pattern: $SINK($USER_INPUT)
        message: "Violation message"
```

## Field Validation

All models use **strict validation** (`extra="forbid"`). This means:

✅ **Valid**: Only documented fields are allowed
❌ **Invalid**: Unknown fields will cause a validation error

**Example of rejected spec:**
```yaml
check:
  type: "forbidden"
  pattern: "print(...)"
  exclude_paths:  # ← ERROR: Not a valid field!
    - "tests/**"
```

**Error message:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for RuleCheck
exclude_paths
  Extra inputs are not permitted [type=extra_forbidden]
```

## Path Filtering

**Note**: Path filtering (e.g., excluding `tests/**`) is **not currently supported** in the high-level DSL.

**Workarounds:**
1. Use `type: raw` with Semgrep's native path filtering:
   ```yaml
   check:
     type: "raw"
     engine: "semgrep"
     config: |
       rules:
         - id: arch-001-impl
           pattern: print(...)
           paths:
             exclude:
               - "tests/**"
   ```

2. Filter results in CI/post-processing

3. Use baseline management to ignore known violations in test files

## Examples

See the `examples/` directory for complete working examples:
- `ARCH-001.yaml`: must_wrap example (HTTP resilience)
- `ARCH-002.yaml`: required_with example (health checks)
- `ARCH-003.yaml`: forbidden example (no print statements)

## Creating New Rules

1. Copy an example file as a template
2. Update all fields to match your rule
3. Test with `ling second-shift --dry-run` to see compiled Semgrep rules
4. Validate with `ling second-shift` to check for violations

## Schema Version

Current schema version: **1**

The `schema_version` field is reserved for future compatibility. Always set it to `1`.
