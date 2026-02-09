---
title: "ARCH-003: Logging Standards"
weight: 2
---

# ARCH-003: Use Logging Instead of Print

**Category**: Code Quality | **Severity**: Warning | **Type**: Enforcement

## The Problem

```python
# ❌ Common mistake
print("Processing user:", user_id)
print(f"API call failed: {error}")
```

This breaks production systems because:
- Can't filter by log level (everything is INFO)
- Can't route to different outputs (stdout only)
- No structured data (can't search/aggregate)
- Breaks when stdout is redirected

## The Solution

Use proper logging:

```python
# ✅ Structured logging
import logging
logging.info("Processing user", extra={"user_id": user_id})
logging.error("API call failed", exc_info=True, extra={"error": str(error)})

# ✅ Click for CLI output
import click
click.echo("✓ Processing complete", err=False)
click.echo("❌ Operation failed", err=True)
```

## Why This Matters

**Observability**: Logs feed monitoring dashboards. Print statements disappear.

**Debugging**: Structured logs can be searched (`user_id=123`). Print statements require manual grep.

**Control**: Log levels let you adjust verbosity in production. Print is all-or-nothing.

## Configuration

Built-in rule. To customize severity:

```bash
sine init --copy-built-in-rules
# Edit .sine-rules/ARCH-003.yaml
# Change severity: "warning" → "error" or "info"
```

## References

- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Click Documentation](https://click.palletsprojects.com/)
- [Structured Logging Best Practices](https://www.structlog.org/)
