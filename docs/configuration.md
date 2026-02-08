# Configuration

Sine supports modern configuration via `pyproject.toml` (recommended for Python projects) or a standalone `sine.toml`.

## Configuration Resolution

Sine resolves configuration in the following order (highest priority first):
1. **CLI Flags**: Arguments passed directly to the command (e.g., `--format json`).
2. **`sine.toml`**: A standalone TOML file in the project root.
3. **`pyproject.toml`**: The standard Python configuration file (under `[tool.sine]`).

## Options Reference

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rules_dir` | Path | `"rules"` | Directory containing Sine Rule Specs (`.yaml`). |
| `patterns_dir` | Path | `".sine-patterns"` | Directory for storing discovered/validated patterns. |
| `target` | List[Path] | `["."]` | Default paths to analyze if none provided via CLI. |
| `format` | String | `"text"` | Output format: `"text"`, `"json"`, or `"sarif"`. |

## Examples

### `pyproject.toml` (Recommended)

```toml
[tool.sine]
rules_dir = "governance/rules"
patterns_dir = "governance/patterns"
target = ["src", "lib"]
format = "text"
```

### `sine.toml`

```toml
rules_dir = "rules"
target = ["."]
format = "sarif"
```
