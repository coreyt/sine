---
title: "ARCH-001: HTTP Resilience"
weight: 1
---

# ARCH-001: HTTP Resilience Wrappers

**Category**: Resilience | **Severity**: Error | **Type**: Enforcement

## Purpose
Prevents cascading failures by ensuring HTTP calls use circuit breakers or retry logic.

## Examples

❌ **Violation:**
```python
response = requests.get("https://api.example.com/data")
```

✅ **Compliant:**
```python
with circuit_breaker():
    response = requests.get("https://api.example.com/data")
```
