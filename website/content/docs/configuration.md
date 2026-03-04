---
title: "Configuration"
weight: 3
---

# Configuration

Lookout uses `lookout.toml` or `pyproject.toml` (for Python projects).

## Minimal Configuration

Lookout works without configuration (uses built-in rules):

```bash
lookout check  # Uses all defaults
```

## Basic Configuration

### Option 1: `pyproject.toml` (Python projects)

```toml
[tool.lookout]
target = ["src", "tests"]
format = "text"
```

### Option 2: `lookout.toml` (Any project)

```toml
target = ["."]
format = "json"
rules_dir = ".lookout-rules"
```

## Configuration Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `rules_dir` | Path | `".lookout-rules"` | User rules directory (optional) |
| `target` | List[Path] | `["."]` | Directories to analyze |
| `format` | String | `"text"` | Output: `text`, `json`, or `sarif` |
| `patterns_dir` | Path | `".lookout-patterns"` | Discovered patterns storage |
| `repo` | String | `null` | GitHub repo for context |

## Rule Loading

Lookout uses hierarchical rule loading (ESLint-style):

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
[tool.lookout]
target = ["src", "lib", "tests"]
```

### Custom Rules Directory

```toml
[tool.lookout]
rules_dir = "governance/architectural-rules"
```

### CI/CD-Friendly

```toml
[tool.lookout]
format = "sarif"  # For GitHub Code Scanning
fail_on_rule_error = true  # Exit 1 on parse errors
```

## Environment Variables

- `GITHUB_TOKEN`: For pattern discovery rate limits

## Next Steps

- [Writing Custom Rules](/docs/custom-rules/)
- [Pattern Catalog](/patterns/)
