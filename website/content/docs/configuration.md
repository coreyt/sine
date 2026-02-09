---
title: "Configuration"
weight: 3
---

# Configuration

Sine uses `sine.toml` or `pyproject.toml` (for Python projects).

## Minimal Configuration

Sine works without configuration (uses built-in rules):

```bash
sine check  # Uses all defaults
```

## Basic Configuration

### Option 1: `pyproject.toml` (Python projects)

```toml
[tool.sine]
target = ["src", "tests"]
format = "text"
```

### Option 2: `sine.toml` (Any project)

```toml
target = ["."]
format = "json"
rules_dir = ".sine-rules"
```

## Configuration Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `rules_dir` | Path | `".sine-rules"` | User rules directory (optional) |
| `target` | List[Path] | `["."]` | Directories to analyze |
| `format` | String | `"text"` | Output: `text`, `json`, or `sarif` |
| `patterns_dir` | Path | `".sine-patterns"` | Discovered patterns storage |
| `repo` | String | `null` | GitHub repo for context |

## Rule Loading

Sine uses hierarchical rule loading (ESLint-style):

1. **Built-in rules** (always loaded, 7 rules included)
2. **User rules** from `rules_dir` (if exists)
3. User rules **override** built-in by ID

Example:

```
Built-in:  ARCH-001, ARCH-003, PATTERN-DISC-006, ...
User:      ARCH-001 (custom), CUSTOM-001
Result:    ARCH-001 (user version), ARCH-003, PATTERN-DISC-006, ..., CUSTOM-001
```

## Advanced Configuration

### Multiple Target Directories

```toml
[tool.sine]
target = ["src", "lib", "tests"]
```

### Custom Rules Directory

```toml
[tool.sine]
rules_dir = "governance/architectural-rules"
```

### CI/CD-Friendly

```toml
[tool.sine]
format = "sarif"  # For GitHub Code Scanning
fail_on_rule_error = true  # Exit 1 on parse errors
```

## Environment Variables

- `GITHUB_TOKEN`: For pattern discovery rate limits

## Next Steps

- [Writing Custom Rules](/docs/custom-rules/)
- [Pattern Catalog](/patterns/)
