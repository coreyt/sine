# Configuration

Sine supports modern configuration via `pyproject.toml` (recommended for Python projects) or a standalone `sine.toml`.

## Quick Setup

The easiest way to configure Sine is with the interactive setup:

```bash
sine init
```

This will:
- Auto-detect your project type (Python, TypeScript, etc.)
- Create configuration file (`sine.toml` or add to `pyproject.toml`)
- Set up `.sine-rules` directory (optional)
- Optionally copy built-in rules for customization

## Built-In Rules

Sine ships with 7 curated architectural rules that work out-of-box:

**Enforcement Rules (ARCH):**
- `ARCH-001`: HTTP calls require resilience wrappers
- `ARCH-003`: Use logging instead of print statements

**Pattern Discovery Rules (PATTERN-DISC):**
- `PATTERN-DISC-006`: Adapter pattern
- `PATTERN-DISC-010`: Pipeline pattern
- `PATTERN-DISC-011`: Dependency Injection
- `PATTERN-DISC-012`: Context managers
- `PATTERN-DISC-015`: Exception hierarchy

These rules are always available and don't need to be in your project directory.

## Configuration Resolution

Sine resolves configuration in the following order (highest priority first):
1. **CLI Flags**: Arguments passed directly to the command (e.g., `--format json`).
2. **`sine.toml`**: A standalone TOML file in the project root.
3. **`pyproject.toml`**: The standard Python configuration file (under `[tool.sine]`).

## Options Reference

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rules_dir` | Path | `".sine-rules"` | Directory containing user-defined Rule Specs (`.yaml`). Built-in rules are always loaded. |
| `patterns_dir` | Path | `".sine-patterns"` | Directory for storing discovered/validated patterns. |
| `target` | List[Path] | `["."]` | Default paths to analyze if none provided via CLI. |
| `format` | String | `"text"` | Output format: `"text"`, `"json"`, or `"sarif"`. |

## Examples

### `pyproject.toml` (Recommended for Python projects)

```toml
[tool.sine]
rules_dir = ".sine-rules"
target = ["src", "tests"]
format = "text"
```

### `sine.toml` (Standalone configuration)

```toml
rules_dir = ".sine-rules"
target = ["."]
format = "text"
```

### Minimal Configuration

You can omit `rules_dir` entirely to use only built-in rules:

```toml
[tool.sine]
target = ["src"]
format = "text"
```

## Rule Loading

Sine uses ESLint-style hierarchical rule loading:

1. **Built-in rules** are always loaded from the package
2. **User rules** are loaded from `rules_dir` (if it exists)
3. If a user rule has the same ID as a built-in rule, the user rule overrides it

This means:
- Sine works immediately without any local rules
- You can customize or override built-in rules by creating rules with matching IDs
- You can add organization-specific rules in `.sine-rules/`

## Migration from Old Default

**Prior to v0.2.0**, the default `rules_dir` was `"rules"`. If you have an existing project:

- **If you have a config file**: No changes needed (explicit `rules_dir` preserved)
- **If you don't have a config**: Run `sine init` or create `sine.toml` with `rules_dir = "rules"`
