"""Tests for batch result parser."""

from __future__ import annotations

import pytest

from lookout.batch.parser import parse_framework_output, parse_language_generic_output


class TestParseLanguageGenericOutput:
    def test_parse_forbidden_check(self) -> None:
        output = """
### Language: `python`

| Field | Value |
|-------|-------|
| **Language** | `python` |
| **Version constraint** | `[SKIP]` |

#### Generic Variant

**Check type**: `forbidden`

**Semgrep pattern(s)**:
```yaml
eval($X)
```

**Good example** (code that FOLLOWS the pattern):
```python
result = ast.literal_eval(user_input)
```

**Bad example** (code that VIOLATES the pattern):
```python
result = eval(user_input)
```
"""
        check, examples = parse_language_generic_output(output)
        assert check.type == "forbidden"
        assert check.pattern == "eval($X)"
        assert len(examples.good) == 1
        assert len(examples.bad) == 1
        assert "literal_eval" in examples.good[0].code
        assert examples.good[0].language == "python"

    def test_parse_raw_check(self) -> None:
        output = """
### Language: `typescript`

#### Generic Variant

**Check type**: `raw`

**Semgrep pattern(s)**:
```yaml
rules:
  - id: di-001-typescript-impl
    languages: [typescript]
    severity: WARNING
    message: Use constructor injection
    patterns:
      - pattern: new $CLASS(...)
      - pattern-not-inside: constructor($...PARAMS) { ... }
```

**Good example**:
```typescript
class Service {
  constructor(private dep: Dep) {}
}
```

**Bad example**:
```typescript
class Service {
  method() {
    const dep = Container.get(Dep);
  }
}
```
"""
        check, examples = parse_language_generic_output(output)
        assert check.type == "raw"
        assert "di-001-typescript-impl" in check.config
        assert examples.good[0].language == "typescript"

    def test_parse_must_wrap_check(self) -> None:
        output = """
#### Generic Variant

**Check type**: `must_wrap`

**Semgrep pattern(s)**:
```yaml
target:
  - requests.get(...)
  - requests.post(...)
wrapper:
  - "circuit_breaker(...)"
```

**Good example**:
```python
with circuit_breaker():
    requests.get(url)
```

**Bad example**:
```python
requests.get(url)
```
"""
        check, examples = parse_language_generic_output(output)
        assert check.type == "must_wrap"
        assert "requests.get(...)" in check.target
        assert "requests.post(...)" in check.target
        assert "circuit_breaker(...)" in check.wrapper

    def test_parse_required_with_check(self) -> None:
        output = """
#### Generic Variant

**Check type**: `required_with`

**Semgrep pattern(s)**:
```yaml
if_present: "@app.route"
must_have: "@require_auth"
```

**Good example**:
```python
@app.route("/api")
@require_auth
def endpoint():
    pass
```

**Bad example**:
```python
@app.route("/api")
def endpoint():
    pass
```
"""
        check, examples = parse_language_generic_output(output)
        assert check.type == "required_with"
        assert check.if_present == "@app.route"
        assert check.must_have == "@require_auth"

    def test_missing_check_type_raises(self) -> None:
        output = "No check type here"
        with pytest.raises(ValueError, match="check type"):
            parse_language_generic_output(output)


class TestParseFrameworkOutput:
    def test_skip_output(self) -> None:
        output = """
SKIP: The generic python variant adequately covers django usage.
Reason: Django's DI patterns are handled by the generic constructor injection rule.
"""
        result = parse_framework_output(output, "python")
        assert result is None

    def test_framework_variant(self) -> None:
        output = """
### Framework: `django` (Language: `python`)

**Why a separate variant?**
> Django uses class-based views with specific DI patterns.

**Check type**: `forbidden`

**Semgrep pattern(s)**:
```yaml
from django.conf import settings
```

**Good example**:
```python
class MyView(View):
    def __init__(self, service: Service):
        self.service = service
```

**Bad example**:
```python
class MyView(View):
    def get(self, request):
        service = Service()
```
"""
        result = parse_framework_output(output, "python")
        assert result is not None
        check, examples = result
        assert check.type == "forbidden"
        assert examples.bad[0].language == "python"
