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
pip install lookout
```

## Install from Source

```bash
git clone https://github.com/coreyt/lookout
cd lookout
pip install -e .
```

## Verify Installation

```bash
lookout --version
# lookout, version 0.2.0

lookout check --help
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
