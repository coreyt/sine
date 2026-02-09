---
title: "Quick Start"
weight: 2
---

# Quick Start Guide

Get up and running with Sine in 5 minutes.

## Step 1: Install

```bash
pip install sine
```

## Step 2: Initialize (Optional)

Sine works immediately with built-in rules, but you can customize:

```bash
cd your-project
sine init

# Interactive prompts:
# ✓ Use pyproject.toml? Yes
# ✓ Target directories? src,tests
# ✓ Output format? text
# ✓ Copy built-in rules for customization? No
```

Creates configuration:

```toml
# pyproject.toml
[tool.sine]
rules_dir = ".sine-rules"
target = ["src", "tests"]
format = "text"
```

## Step 3: Run Your First Check

```bash
sine check
```

Example output:

```
✓ Checking 47 files against 7 rules...

❌ src/api/client.py:23
   HTTP call outside resilience wrapper (ARCH-001)
   
   22: def fetch_user_data(user_id):
   23:     response = requests.get(f"{API_URL}/users/{user_id}")
   24:     return response.json()
   
   Suggestion: Wrap with circuit_breaker() or @resilient decorator

⚠️  src/utils/debug.py:15
   Use logging instead of print() (ARCH-003)
   
   14: def log_request(method, url):
   15:     print(f"{method} {url}")
   16: 
   
   Suggestion: Use logging.info() or click.echo()

2 violations found
```

## Step 4: Discover Patterns

Find existing patterns in your codebase:

```bash
sine discover
```

Output shows pattern instances for documentation:

```
Pattern Discovery Results:

PATTERN-DISC-011 (Dependency Injection): 3 instances
  ├─ src/services/user_service.py:8
  │  Constructor injection of UserRepository
  ├─ src/handlers/api.py:12
  │  Function parameter injection
  └─ src/app.py:45
     Configuration-based injection

PATTERN-DISC-012 (Context Managers): 5 instances
  └─ src/database.py:23, src/cache.py:15, ...
```

## Step 5: CI/CD Integration

Add to your GitHub Actions:

```yaml
name: Architecture Check

on: [push, pull_request]

jobs:
  sine:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install sine
      - run: sine check --format sarif > results.sarif
      - uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

## Next Steps

- [Configuration Options](/docs/configuration/)
- [Pattern Catalog](/patterns/)
- [Writing Custom Rules](/docs/custom-rules/)
