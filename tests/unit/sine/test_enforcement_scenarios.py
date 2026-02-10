from __future__ import annotations

import tempfile
from pathlib import Path
from textwrap import dedent

from sine.models import (
    ForbiddenCheck,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)
from sine.runner import run_sine


def _create_di_rule() -> RuleSpecFile:
    """Creates a rule that strictly forbids instantiating classes inside __init__."""
    return RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="ARCH-DI-001",
            title="Enforce Dependency Injection",
            description="Dependencies must be injected, not instantiated.",
            rationale="Tight coupling prevents testing and flexibility.",
            tier=1,
            category="architecture",
            severity="error",
            languages=["python"],
            check=ForbiddenCheck(
                type="forbidden",
                pattern=dedent("""
                    class $C:
                        ...
                        def __init__(self, ...):
                            ...
                            self.$FIELD = $CLASS(...)
                """).strip(),
            ),
            reporting=RuleReporting(
                default_message="Hardcoded dependency detected. Inject this dependency instead.",
                confidence="high",
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )


def test_enforce_dependency_injection_violation():
    """Negative Test: Ensure code WITHOUT DI is flagged as a violation."""
    bad_code = dedent("""
        class UserManager:
            def __init__(self):
                # VIOLATION: Hardcoded dependency
                self.db = DatabaseConnection("localhost")

            def get_user(self, id):
                return self.db.query(id)
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "bad_di.py"
        target_path.write_text(bad_code, encoding="utf-8")

        findings, _, _, _, _ = run_sine(
            specs=[_create_di_rule()],
            targets=[target_path],
        )

        assert len(findings) == 1
        assert findings[0].guideline_id == "ARCH-DI-001"
        assert findings[0].file == str(target_path)
        assert "Hardcoded dependency detected" in findings[0].message


def test_enforce_dependency_injection_compliance():
    """Positive Test: Ensure code WITH DI passes."""
    good_code = dedent("""
        class UserManager:
            def __init__(self, db: DatabaseConnection):
                # COMPLIANT: Injected dependency
                self.db = db

            def get_user(self, id):
                return self.db.query(id)
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "good_di.py"
        target_path.write_text(good_code, encoding="utf-8")

        findings, _, _, _, _ = run_sine(
            specs=[_create_di_rule()],
            targets=[target_path],
        )

        assert len(findings) == 0
