---
title: "Installation"
weight: 1
---

# Installation

## Requirements

- **Python 3.10+**
- **Semgrep** (installed automatically as dependency)

## Install from PyPI

```bash
pip install sine
```

## Install from Source

```bash
git clone https://github.com/coreyt/sine
cd sine
pip install -e .
```

## Verify Installation

```bash
sine --version
# sine, version 0.2.0

sine check --help
# Shows available commands
```

## Optional: GitHub Token

For pattern discovery (if using external sources):

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Rate limits:
- Without token: 60 requests/hour
- With token: 5,000 requests/hour

[Next: Quick Start →](/docs/quickstart/)
